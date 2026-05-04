"""File reading tool for the docchat agent."""
from tools import is_path_safe

SCHEMA = {
    "type": "function",
    "function": {
        "name": "cat",
        "description": "Read and return the contents of a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read.",
                }
            },
            "required": ["path"],
        },
    },
}


def cat(path):
    """
    Return the text contents of a file, or an error message on failure.

    >>> cat('test_data/hello.txt')
    'Hello, World!'
    >>> cat('test_data/numbers.txt')
    'one\\ntwo\\nthree'
    >>> cat('/etc/passwd')
    'Error: path is not safe'
    >>> cat('../secret')
    'Error: path is not safe'
    >>> cat('no_such_file_xyz.txt')
    'Error: file not found: no_such_file_xyz.txt'
    >>> cat('test_data/binary.bin')
    'Error: cannot decode file: test_data/binary.bin'
    """
    if not is_path_safe(path):
        return 'Error: path is not safe'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f'Error: file not found: {path}'
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='utf-16') as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            return f'Error: cannot decode file: {path}'
