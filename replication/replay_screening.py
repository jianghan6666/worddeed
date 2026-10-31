"""Run the frozen screening replay with platform-independent path/text encoding.

Only JSON line endings and package-relative path separators are specified here.
The frozen scientific code and its byte-for-byte output checks are unchanged.
"""
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1] / 'study/screening/experiment/results-2026-10-21'


def main():
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location('_frozen_replay', HERE / 'replay.py')
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    def write_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
                        encoding='utf8', newline='\n')
    def package_binding(path):
        path = replay.resolve(path).resolve()
        return {'path': path.relative_to(HERE).as_posix(), 'sha256': replay.digest(path)}
    replay.write_json = write_json
    replay.package_binding = package_binding
    replay.main()


if __name__ == '__main__':
    main()
