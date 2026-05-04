"""Directory listing tool for the docchat agent."""
import glob
from tools import is_path_safe


SCHEMA = {
    "type": "function",
    "function": {
        "name": "ls",
        "description": "List the files and folders in a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory to list. Defaults to current directory.",
                }
            },
            "required": [],
        },
    },
}


def ls(path='.'):
    """
    Return a sorted, newline-separated list of entries in a directory.

    >>> ls('test_data')
    'binary.bin\\nhello.txt\\nnumbers.txt\\ntest.png'
    >>> ls('.')  # doctest: +ELLIPSIS
    '...'
    >>> ls('/etc')
    'Error: path is not safe'
    >>> ls('../secret')
    'Error: path is not safe'
    >>> ls('nonexistent_xyz_dir')
    'Error: no such directory: nonexistent_xyz_dir'
    """
    if not is_path_safe(path):
        return 'Error: path is not safe'
    entries = sorted(glob.glob(path + '/*'))
    if not entries and path != '.':
        import os
        if not os.path.isdir(path):
            return f'Error: no such directory: {path}'
    return '\n'.join(e.split('/')[-1] for e in entries)
