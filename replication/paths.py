"""Resolve historical inventory paths without changing frozen archive identities."""
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MOVES = sorted(json.loads((ROOT / 'replication/paths.json').read_text())['moves'],
               key=lambda item: len(item['from']), reverse=True)


def current_path(name):
    """Return the current repository-relative path for an old or current name."""
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise ValueError('Expected a repository-relative POSIX path: ' + name)
    for item in MOVES:
        old = item['from']
        if name == old or name.startswith(old + '/'):
            return item['to'] + name[len(old):]
    return name


def repository_path(name):
    return ROOT / current_path(name)
