"""File removal tool for the docchat agent."""
import glob as _glob
import os
import subprocess
from tools import is_path_safe

SCHEMA = {
    "type": "function",
    "function": {
        "name": "rm",
        "description": "Delete files matching a path or glob and commit the removal.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path or glob pattern to delete.",
                }
            },
            "required": ["path"],
        },
    },
}


def rm(path):
    """
    Delete all files matching path (supports globs) and commit the removal.

    >>> rm('/etc/passwd')
    'Error: path is not safe'
    >>> rm('../secret')
    'Error: path is not safe'
    >>> rm('nonexistent_xyz_file.txt')
    'Error: no files matched: nonexistent_xyz_file.txt'
    """
    if not is_path_safe(path):
        return 'Error: path is not safe'

    matches = sorted(_glob.glob(path))
    if not matches:
        return f'Error: no files matched: {path}'

    removed = []
    for fpath in matches:
        try:
            os.remove(fpath)
            removed.append(fpath)
        except OSError as e:
            return f'Error removing {fpath}: {e}'

    subprocess.run(
        ['git', 'rm', '--cached'] + removed,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ['git', 'commit', '-m', f'[docchat] rm {path}'],
        capture_output=True,
        text=True,
    )
    return f'Removed: {", ".join(removed)}'
