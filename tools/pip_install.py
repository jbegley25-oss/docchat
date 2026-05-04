"""pip install tool for the docchat agent (extra credit)."""
import subprocess
import sys

SCHEMA = {
    "type": "function",
    "function": {
        "name": "pip_install",
        "description": "Install a Python package using pip.",
        "parameters": {
            "type": "object",
            "properties": {
                "library_name": {
                    "type": "string",
                    "description": "The PyPI package name to install.",
                }
            },
            "required": ["library_name"],
        },
    },
}


def pip_install(library_name):
    """
    Install a Python package and return the pip output.

    Only accepts simple package names (no slashes or path traversal).

    >>> pip_install('../evil')
    'Error: invalid package name: ../evil'
    >>> pip_install('/bin/bash')
    'Error: invalid package name: /bin/bash'
    >>> 'already satisfied' in pip_install('pip') or 'Successfully' in pip_install('pip')
    True
    """
    if '/' in library_name or '..' in library_name:
        return f'Error: invalid package name: {library_name}'
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', library_name],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    return output.strip() if output.strip() else 'Done.'
