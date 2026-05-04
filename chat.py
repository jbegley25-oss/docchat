"""Docchat: an AI agent that lets you chat with the files in your current directory."""
import glob as _glob
import json
import os
import tempfile
from dotenv import load_dotenv
from groq import Groq
import tools.calculate
import tools.ls
import tools.cat
import tools.grep
import tools.compact
import tools.load_image

load_dotenv()

_GROQ_TEXT_MODEL = 'llama-3.1-8b-instant'
_GROQ_VISION_MODEL = 'meta-llama/llama-4-scout-17b-16e-instruct'
_PROVIDER_MODELS = {
    'groq': _GROQ_TEXT_MODEL,
    'openai': 'openai/gpt-4o',
    'anthropic': 'anthropic/claude-opus-4-5',
    'google': 'google/gemini-2.0-flash-001',
}

TOOLS = [
    tools.calculate.SCHEMA,
    tools.ls.SCHEMA,
    tools.cat.SCHEMA,
    tools.grep.SCHEMA,
    tools.compact.SCHEMA,
    tools.load_image.SCHEMA,
]


def _make_client(provider='groq'):
    """
    Create an API client for the given provider.

    Groq is used directly; all other providers route through OpenRouter.

    >>> _make_client('groq').__class__.__name__
    'Groq'
    """
    if provider == 'groq':
        return Groq()
    from openai import OpenAI
    return OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=os.environ.get('OPENROUTER_API_KEY', 'not-set'),
    )


def _run_tool(name, args, messages=None, client=None):
    """
    Dispatch a named tool call and return its string result.

    >>> _run_tool('calculate', {'expression': '3 * 7'})
    '21'
    >>> _run_tool('ls', {'path': 'test_data'})
    'binary.bin\\nhello.txt\\nnumbers.txt\\ntest.png'
    >>> _run_tool('cat', {'path': 'test_data/hello.txt'})
    'Hello, World!'
    >>> _run_tool('grep', {'pattern': 'World', 'path': 'test_data/hello.txt'})
    'Hello, World!'
    >>> _run_tool('ls', {})  # doctest: +ELLIPSIS
    '...'
    >>> _run_tool('load_image', {'path': 'test_data/hello.txt'})
    'Error: load_image requires an active chat session'
    >>> _run_tool('compact', {})
    'Error: compact requires an active chat session'
    >>> _run_tool('unknown', {})
    'Error: unknown tool: unknown'
    """
    if name == 'calculate':
        return tools.calculate.calculate(args['expression'])
    if name == 'ls':
        return tools.ls.ls(args.get('path', '.'))
    if name == 'cat':
        return tools.cat.cat(args['path'])
    if name == 'grep':
        return tools.grep.grep(args['pattern'], args['path'])
    if name == 'load_image':
        if messages is None:
            return 'Error: load_image requires an active chat session'
        return tools.load_image.load_image(args['path'], messages)
    if name == 'compact':
        if messages is None or client is None:
            return 'Error: compact requires an active chat session'
        summary = tools.compact.compact(messages, client)
        if messages:
            system = messages[0]
            messages.clear()
            messages.append(system)
            messages.append({'role': 'assistant', 'content': f'[Summary]: {summary}'})
        return summary
    return f'Error: unknown tool: {name}'


def _speak(client, text):
    """Convert text to speech using Groq TTS and play it through the speakers."""
    try:
        import sounddevice as sd
        import soundfile as sf
        import io
    except ImportError:
        return
    try:
        response = client.audio.speech.create(
            model='playai-tts',
            voice='Fritz-PlayAI',
            input=text,
            response_format='wav',
        )
        data, samplerate = sf.read(io.BytesIO(response.read()))
        sd.play(data, samplerate)
        sd.wait()
    except Exception as e:
        print(f'[tts error] {e}')


def _transcribe(client):
    """Record microphone audio until Enter is pressed and return the transcription."""
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError:
        print('[stt] sounddevice/soundfile not installed; falling back to text input')
        return input('chat> ')

    chunks = []
    samplerate = 16000

    def _cb(indata, frames, time, status):
        chunks.append(indata.copy())

    print('chat> [Press Enter to start recording]', end='', flush=True)
    input()
    with sd.InputStream(samplerate=samplerate, channels=1, dtype='float32', callback=_cb):
        print('[Recording... Press Enter to stop]', end='', flush=True)
        input()

    if not chunks:
        return ''

    audio = np.concatenate(chunks, axis=0)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp = f.name
        sf.write(f, audio, samplerate)
    try:
        with open(tmp, 'rb') as f:
            result = client.audio.transcriptions.create(
                file=('audio.wav', f, 'audio/wav'),
                model='whisper-large-v3-turbo',
            )
        text = result.text
        print(f'[transcribed] {text}')
        return text
    except Exception as e:
        print(f'[stt error] {e}')
        return ''
    finally:
        os.unlink(tmp)


class Chat:
    """
    An AI chat session backed by Groq or OpenRouter with file-aware tool support.

    Maintains a running message history and automatically dispatches tool calls
    before yielding the final reply. Supports TTS output, STT input, tab
    completion, and multiple AI providers via the --provider flag.

    >>> chat = Chat()
    >>> isinstance(chat.send_message('say the single word: hello', temperature=0.0), str)
    True
    >>> len(chat.messages) >= 3
    True
    >>> Chat(debug=True).debug
    True
    >>> Chat(provider='openai').provider
    'openai'
    >>> Chat(tts=True).tts
    True
    """

    def __init__(self, debug=False, provider='groq', tts=False, stt=False):
        """Initialize a chat session with the given options."""
        self.debug = debug
        self.provider = provider
        self.tts = tts
        self.stt = stt
        self.client = _make_client(provider)
        self.messages = [
            {
                'role': 'system',
                'content': (
                    'You are a helpful assistant. Answer in 1-3 sentences. '
                    'Only use tools when the user explicitly asks you to list '
                    'files, read files, search files, or calculate something. '
                    'Always use relative paths when calling tools.'
                ),
            }
        ]

    def _model(self):
        """Return the model ID appropriate for the current message history."""
        has_images = any(
            isinstance(m.get('content'), list)
            for m in self.messages
            if isinstance(m, dict)
        )
        if self.provider == 'groq' and has_images:
            return _GROQ_VISION_MODEL
        return _PROVIDER_MODELS[self.provider]

    def send_message(self, message, temperature=0.8):
        """
        Append a user message, execute any tool calls, and return the final reply.
        """
        self.messages.append({'role': 'user', 'content': message})
        while True:
            try:
                completion = self.client.chat.completions.create(
                    messages=self.messages,
                    model=self._model(),
                    temperature=temperature,
                    tools=TOOLS,
                )
            except Exception as e:
                if 'tool_use_failed' in str(e):
                    completion = self.client.chat.completions.create(
                        messages=self.messages,
                        model=self._model(),
                        temperature=temperature,
                        tools=TOOLS,
                    )
                else:
                    raise
            choice = completion.choices[0]
            if choice.finish_reason == 'tool_calls':
                self.messages.append(choice.message)
                for call in choice.message.tool_calls:
                    name = call.function.name
                    call_args = json.loads(call.function.arguments)
                    if self.debug:
                        arg_str = ' '.join(str(v) for v in call_args.values())
                        print(f'[tool] /{name} {arg_str}'.rstrip())
                    result = _run_tool(
                        name, call_args,
                        messages=self.messages,
                        client=self.client,
                    )
                    self.messages.append({
                        'role': 'tool',
                        'tool_call_id': call.id,
                        'content': result,
                    })
            else:
                reply = choice.message.content
                self.messages.append({'role': 'assistant', 'content': reply})
                if self.tts:
                    _speak(self.client, reply)
                return reply


def _handle_slash(command, chat=None):
    """
    Parse and execute a slash command, returning the output as a string.

    >>> _handle_slash('/ls test_data')
    'binary.bin\\nhello.txt\\nnumbers.txt\\ntest.png'
    >>> _handle_slash('/cat test_data/hello.txt')
    'Hello, World!'
    >>> _handle_slash('/calculate 6 * 7')
    '42'
    >>> _handle_slash('/grep World test_data/hello.txt')
    'Hello, World!'
    >>> _handle_slash('/')
    'Error: empty command'
    >>> _handle_slash('/cat')
    'Error: cat requires a file path'
    >>> _handle_slash('/grep World')
    'Error: grep requires a pattern and path'
    >>> _handle_slash('/compact')
    'Error: compact requires an active chat session'
    >>> isinstance(_handle_slash('/compact', chat=Chat()), str)
    True
    >>> _handle_slash('/load_image')
    'Error: load_image requires a file path'
    >>> _handle_slash('/load_image nonexistent.png')
    'Error: file not found: nonexistent.png'
    >>> _handle_slash('/load_image test_data/hello.txt')
    'Error: load_image requires an active chat session'
    >>> _handle_slash('/load_image test_data/test.png', chat=Chat())
    'Image loaded: test_data/test.png'
    >>> _handle_slash('/bogus arg')
    'Error: unknown command: bogus'
    """
    parts = command[1:].split()
    if not parts:
        return 'Error: empty command'
    cmd, args = parts[0], parts[1:]
    if cmd == 'calculate':
        return tools.calculate.calculate(' '.join(args))
    if cmd == 'ls':
        return tools.ls.ls(args[0] if args else '.')
    if cmd == 'cat':
        if not args:
            return 'Error: cat requires a file path'
        return tools.cat.cat(args[0])
    if cmd == 'grep':
        if len(args) < 2:
            return 'Error: grep requires a pattern and path'
        return tools.grep.grep(args[0], args[1])
    if cmd == 'compact':
        if chat is None:
            return 'Error: compact requires an active chat session'
        return _run_tool('compact', {}, messages=chat.messages, client=chat.client)
    if cmd == 'load_image':
        if not args:
            return 'Error: load_image requires a file path'
        if not os.path.isfile(args[0]):
            return f'Error: file not found: {args[0]}'
        if chat is None:
            return 'Error: load_image requires an active chat session'
        return tools.load_image.load_image(args[0], chat.messages)
    return f'Error: unknown command: {cmd}'


def _make_completer():
    """
    Return a readline-compatible tab completer for slash commands and file paths.

    Completes command names when the text starts with '/', otherwise
    completes file and directory names using glob.

    >>> completer = _make_completer()
    >>> completer('/l', 0)
    '/load_image'
    >>> completer('/l', 1)
    '/ls'
    >>> completer('/l', 2) is None
    True
    >>> completer('/ca', 0)
    '/calculate'
    >>> completer('/ca', 1)
    '/cat'
    >>> completer('/ca', 2) is None
    True
    >>> completer('test_data/h', 0)
    'test_data/hello.txt'
    >>> completer('nonexistent_path_xyz', 0) is None
    True
    """
    commands = sorted(['calculate', 'cat', 'compact', 'grep', 'load_image', 'ls'])

    def completer(text, state):
        if text.startswith('/'):
            prefix = text[1:]
            matches = ['/' + c for c in commands if c.startswith(prefix)]
        else:
            paths = sorted(_glob.glob(text + '*'))
            matches = [p + ('/' if os.path.isdir(p) else '') for p in paths]
        try:
            return matches[state]
        except IndexError:
            return None

    return completer


def repl(temperature=0.8, debug=False, tts=False, stt=False, provider='groq'):
    """
    Run the interactive read-eval-print loop.

    Lines starting with '/' execute as slash commands; all other input goes
    to the LLM. Supports TTS, STT, tab completion, and provider selection.

    >>> def fake_input(prompt):
    ...     try:
    ...         line = lines.pop(0)
    ...         print(f'{prompt}{line}')
    ...         return line
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = fake_input

    >>> lines = ['/cat test_data/hello.txt', '/calculate 2 + 2']
    >>> repl(temperature=0.0)
    chat> /cat test_data/hello.txt
    Hello, World!
    chat> /calculate 2 + 2
    4
    <BLANKLINE>

    >>> lines = ['say exactly the word: hello']
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> say exactly the word: hello
    ...
    <BLANKLINE>
    """
    try:
        import readline
        readline.set_completer_delims(' \t\n')
        readline.set_completer(_make_completer())
        readline.parse_and_bind('tab: complete')
    except ImportError:
        pass
    chat = Chat(debug=debug, tts=tts, stt=stt, provider=provider)
    try:
        while True:
            if stt:
                user_input = _transcribe(chat.client)
            else:
                user_input = input('chat> ')
            if not user_input:
                continue
            if user_input.startswith('/'):
                print(_handle_slash(user_input, chat=chat))
            else:
                print(chat.send_message(user_input, temperature=temperature))
    except (KeyboardInterrupt, EOFError):
        print()


def main():
    """Entry point: optional message, --debug, --tts, --stt, and --provider flags."""
    import argparse
    parser = argparse.ArgumentParser(description='Chat with the files in your project.')
    parser.add_argument('message', nargs='?', help='Single message to send')
    parser.add_argument('--debug', action='store_true', help='Print tool calls')
    parser.add_argument('--tts', action='store_true', help='Speak responses aloud')
    parser.add_argument('--stt', action='store_true', help='Accept voice input')
    parser.add_argument(
        '--provider',
        choices=['groq', 'openai', 'anthropic', 'google'],
        default='groq',
        help='LLM provider (default: groq)',
    )
    args = parser.parse_args()
    if args.message:
        chat = Chat(debug=args.debug, tts=args.tts, provider=args.provider)
        print(chat.send_message(args.message))
    else:
        repl(debug=args.debug, tts=args.tts, stt=args.stt, provider=args.provider)


if __name__ == '__main__':
    main()
