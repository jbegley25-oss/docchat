"""Tools package for the docchat agent: file system and calculation utilities."""
import os


def is_path_safe(path):
    """
    Return True only if path is relative and contains no directory traversal.

    >>> is_path_safe('.')
    True
    >>> is_path_safe('subdir/file.txt')
    True
    >>> is_path_safe('test_data/hello.txt')
    True
    >>> is_path_safe('/etc/passwd')
    False
    >>> is_path_safe('..')
    False
    >>> is_path_safe('../secret')
    False
    >>> is_path_safe('a/../../etc/passwd')
    False
    >>> is_path_safe('subdir/../other')
    False
    """
    if os.path.isabs(path):
        return False
    parts = path.replace('\\', '/').split('/')
    return '..' not in parts
