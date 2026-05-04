"""File writing tools for the docchat agent."""
import os
import subprocess
import sys
from tools import is_path_safe

SCHEMA_WRITE_FILE = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write contents to a file, commit it to git, and run doctests "
            "if it is a Python file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to write.",
                },
                "contents": {
                    "type": "string",
                    "description": "UTF-8 text to write to the file.",
                },
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message (prefixed with [docchat]).",
                },
            },
            "required": ["path", "contents", "commit_message"],
        },
    },
}

SCHEMA_WRITE_FILES = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": "Write multiple files at once and commit them all to git.",
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of {path, contents} dicts to write.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                        },
                        "required": ["path", "contents"],
                    },
                },
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message (prefixed with [docchat]).",
                },
            },
            "required": ["files", "commit_message"],
        },
    },
}


def _git(args):
    """Run a git command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ['git'] + args,
        capture_output=True,
        text=True,
    )
    return result.stdout, result.stderr, result.returncode


def _run_doctests(path):
    """Run doctests on path and return output string."""
    result = subprocess.run(
        [sys.executable, '-m', 'doctest', path, '-v'],
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip()


def write_files(files, commit_message):
    """
    Write multiple files and commit them all with a [docchat]-prefixed message.

    Returns a summary of what was written and the git output.

    >>> write_files([], 'empty')
    'Error: no files provided'
    >>> write_files([{'path': '/etc/evil', 'contents': 'x'}], 'bad')
    'Error: path is not safe: /etc/evil'
    >>> write_files([{'path': '../evil', 'contents': 'x'}], 'bad')
    'Error: path is not safe: ../evil'
    """
    if not files:
        return 'Error: no files provided'

    for f in files:
        if not is_path_safe(f['path']):
            return f'Error: path is not safe: {f["path"]}'

    written = []
    for f in files:
        path = f['path']
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(f['contents'])
        written.append(path)

    _git(['add'] + written)
    _, stderr, rc = _git(['commit', '-m', f'[docchat] {commit_message}'])
    if rc != 0:
        commit_out = f'Git error: {stderr.strip()}'
    else:
        commit_out = f'Committed: [docchat] {commit_message}'

    doctest_out = []
    for path in written:
        if path.endswith('.py'):
            doctest_out.append(f'--- doctests: {path} ---\n{_run_doctests(path)}')

    parts = [f'Wrote: {", ".join(written)}', commit_out] + doctest_out
    return '\n'.join(parts)


def write_file(path, contents, commit_message):
    """
    Write a single file, commit it, and run its doctests if it is Python.

    This is a thin wrapper around write_files.

    >>> write_file('/etc/evil', 'x', 'bad')
    'Error: path is not safe: /etc/evil'
    >>> write_file('../evil', 'x', 'bad')
    'Error: path is not safe: ../evil'
    """
    return write_files([{'path': path, 'contents': contents}], commit_message)
