"""Doctest runner tool for the docchat agent."""
import subprocess
import sys
from tools import is_path_safe

SCHEMA = {
    "type": "function",
    "function": {
        "name": "doctests",
        "description": "Run the doctests for a Python file and return the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the Python file to test.",
                }
            },
            "required": ["path"],
        },
    },
}


def doctests(path):
    """
    Run doctests on a Python file with --verbose and return combined output.

    >>> doctests('/etc/passwd')
    'Error: path is not safe'
    >>> doctests('../secret.py')
    'Error: path is not safe'
    >>> out = doctests('tools/calculate.py')
    >>> 'items passed' in out or 'no items' in out
    True
    """
    if not is_path_safe(path):
        return 'Error: path is not safe'
    result = subprocess.run(
        [sys.executable, '-m', 'doctest', path, '-v'],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    return output.strip() if output.strip() else 'No output.'
