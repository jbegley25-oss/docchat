"""Regex search tool for the docchat agent."""
import re
import glob as glob_module
from tools import is_path_safe

SCHEMA = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "Search files matching a glob for lines matching a regex.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "File path or glob pattern to search.",
                },
            },
            "required": ["pattern", "path"],
        },
    },
}


def grep(pattern, path):
    """
    Return all lines matching pattern across files matching the glob path.

    >>> grep('Hello', 'test_data/hello.txt')
    'Hello, World!'
    >>> grep('two', 'test_data/numbers.txt')
    'two'
    >>> grep('nomatch_xyz', 'test_data/hello.txt')
    ''
    >>> grep('Hello', '/etc/passwd')
    'Error: path is not safe'
    >>> grep('Hello', '../secret')
    'Error: path is not safe'
    >>> grep('o', 'test_data/*.txt')  # doctest: +ELLIPSIS
    '...'
    """
    if not is_path_safe(path):
        return 'Error: path is not safe'
    files = sorted(glob_module.glob(path))
    matches = []
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if re.search(pattern, line):
                        matches.append(line.rstrip('\n'))
        except (FileNotFoundError, UnicodeDecodeError):
            pass
    return '\n'.join(matches)
