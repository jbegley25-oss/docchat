"""Docchat: an AI agent that lets you chat with the files in your current directory."""
import json
from groq import Groq, BadRequestError
from dotenv import load_dotenv
import tools.calculate
import tools.ls
import tools.cat
import tools.grep

load_dotenv()

TOOLS = [
    tools.calculate.SCHEMA,
    tools.ls.SCHEMA,
    tools.cat.SCHEMA,
    tools.grep.SCHEMA,
]

_TOOL_NAMES = {t['function']['name'] for t in TOOLS}


def _run_tool(name, args):
    """
    Dispatch a tool call by name and return its string result.

    >>> _run_tool('calculate', {'expression': '3 * 7'})
    '21'
    >>> _run_tool('ls', {'path': 'test_data'})
    'binary.bin\\nhello.txt\\nnumbers.txt'
    >>> _run_tool('cat', {'path': 'test_data/hello.txt'})
    'Hello, World!'
    >>> _run_tool('grep', {'pattern': 'World', 'path': 'test_data/hello.txt'})
    'Hello, World!'
    >>> _run_tool('ls', {})  # doctest: +ELLIPSIS
    '...'
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
    return f'Error: unknown tool: {name}'


class Chat:
    """
    An AI chat session backed by the Groq API with file-aware tool support.

    Maintains a running message history and automatically dispatches tool
    calls returned by the model before yielding the final assistant reply.

    >>> chat = Chat()
    >>> isinstance(chat.send_message('say the single word: hello', temperature=0.0), str)
    True
    >>> len(chat.messages) >= 3
    True
    >>> Chat(debug=True).debug
    True
    """

    def __init__(self, debug=False):
        """Initialize a chat session with an empty history and Groq client."""
        self.debug = debug
        self.client = Groq()
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer in 1-3 sentences. "
                    "Only use tools when the user explicitly asks you to list "
                    "files, read files, search files, or calculate something. "
                    "Always use relative paths when calling tools."
                ),
            }
        ]

    def send_message(self, message, temperature=0.8):
        """
        Append a user message, run any tool calls, and return the final reply.
        """
        self.messages.append({'role': 'user', 'content': message})
        while True:
            try:
                completion = self.client.chat.completions.create(
                    messages=self.messages,
                    model='llama-3.1-8b-instant',
                    temperature=temperature,
                    tools=TOOLS,
                )
            except BadRequestError as e:
                if 'tool_use_failed' in str(e):
                    completion = self.client.chat.completions.create(
                        messages=self.messages,
                        model='llama-3.1-8b-instant',
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
                    result = _run_tool(name, call_args)
                    self.messages.append({
                        'role': 'tool',
                        'tool_call_id': call.id,
                        'content': result,
                    })
            else:
                reply = choice.message.content
                self.messages.append({'role': 'assistant', 'content': reply})
                return reply


def _handle_slash(command, chat=None):
    """
    Parse and execute a slash command, returning the output as a string.

    >>> _handle_slash('/ls test_data')
    'binary.bin\\nhello.txt\\nnumbers.txt'
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
    return f'Error: unknown command: {cmd}'


def repl(temperature=0.8, debug=False):
    """
    Run the interactive read-eval-print loop.

    Lines starting with '/' are handled as slash commands; everything else
    is sent to the LLM.

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
    chat = Chat(debug=debug)
    try:
        while True:
            user_input = input('chat> ')
            if user_input.startswith('/'):
                print(_handle_slash(user_input, chat=chat))
            else:
                print(chat.send_message(user_input, temperature=temperature))
    except (KeyboardInterrupt, EOFError):
        print()


def main():
    """Entry point: optional positional message and --debug flag."""
    import argparse
    parser = argparse.ArgumentParser(description='Chat with the files in your project.')
    parser.add_argument('message', nargs='?', help='Single message to send')
    parser.add_argument('--debug', action='store_true', help='Print tool calls')
    args = parser.parse_args()
    if args.message:
        chat = Chat(debug=args.debug)
        print(chat.send_message(args.message))
    else:
        repl(debug=args.debug)


if __name__ == '__main__':
    main()
