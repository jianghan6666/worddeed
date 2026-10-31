"""Resolve a local analysis executable before starting expensive reproduction."""
from pathlib import Path
import shutil


def resolve_executable(value):
    """Accept a PATH command or an explicit path, including spaces and ~."""
    expanded = str(Path(value).expanduser())
    path = Path(shutil.which(expanded) or expanded).resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f'Analysis executable not found: {value}. Supply its executable file '
            'or a command available on PATH, not an application directory.')
    return str(path)
