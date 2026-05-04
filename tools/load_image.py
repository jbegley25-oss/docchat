"""Image loading tool for the docchat agent."""
import base64
import mimetypes
from tools import is_path_safe

SCHEMA = {
    "type": "function",
    "function": {
        "name": "load_image",
        "description": "Load an image file and add it to the conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the image file to load.",
                }
            },
            "required": ["path"],
        },
    },
}

_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}


def load_image(path, messages):
    """
    Read an image file and append it to messages as a vision content block.

    Returns a status string; the image is added to messages as a side effect.

    >>> load_image('/etc/passwd', [])
    'Error: path is not safe'
    >>> load_image('../secret', [])
    'Error: path is not safe'
    >>> load_image('no_such_file.png', [])
    'Error: file not found: no_such_file.png'
    >>> load_image('test_data/hello.txt', [])
    'Error: unsupported image type: text/plain'
    >>> msgs = []
    >>> load_image('test_data/test.png', msgs)
    'Image loaded: test_data/test.png'
    >>> len(msgs)
    1
    """
    if not is_path_safe(path):
        return 'Error: path is not safe'

    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type or mime_type not in _IMAGE_TYPES:
        label = mime_type if mime_type else 'unknown'
        return f'Error: unsupported image type: {label}'

    try:
        with open(path, 'rb') as f:
            data = base64.standard_b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        return f'Error: file not found: {path}'

    messages.append({
        'role': 'user',
        'content': [
            {
                'type': 'image_url',
                'image_url': {'url': f'data:{mime_type};base64,{data}'},
            }
        ],
    })
    return f'Image loaded: {path}'
