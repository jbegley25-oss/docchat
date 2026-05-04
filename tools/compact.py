"""Chat history compaction tool for the docchat agent."""

SCHEMA = {
    "type": "function",
    "function": {
        "name": "compact",
        "description": (
            "Summarize the conversation history into 1-5 lines to reduce token count. "
            "Call this when the chat history is long."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def compact(messages, client):
    """
    Summarize non-system messages and return the summary string.

    Returns an empty string when there is nothing to summarize.

    >>> compact([], None)
    ''
    >>> compact([{'role': 'system', 'content': 'be helpful'}], None)
    ''
    """
    parts = []
    for m in messages:
        if isinstance(m, dict):
            role = m.get('role', '')
            content = m.get('content', '')
        else:
            role = getattr(m, 'role', '')
            content = getattr(m, 'content', '') or ''
        if role not in ('system', 'tool') and content and isinstance(content, str):
            parts.append(f'{role}: {content}')

    if not parts:
        return ''

    history = '\n'.join(parts)
    response = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': 'Summarize concisely in 1-5 lines.'},
            {'role': 'user', 'content': f'Summarize this chat history:\n{history}'},
        ],
        model='llama-3.1-8b-instant',
        temperature=0.0,
    )
    return response.choices[0].message.content
