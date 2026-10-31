"""Hash-check and stream a multipart review archive without an assembled copy."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


class PartsReader(io.RawIOBase):
    def __init__(self, manifest, directory, acquire=None, release=None):
        self.parts = iter(manifest['parts'])
        self.directory = Path(directory)
        self.current = None
        self.archive_hash = hashlib.sha256()
        self.part = None
        self.acquire = acquire
        self.release = release

    def readable(self):
        return True

    def read(self, size=-1):
        if size < 0:
            raise ValueError('Streaming reads must have a bounded size')
        output = bytearray()
        while len(output) < size:
            if self.current is None:
                self.part = next(self.parts, None)
                if self.part is None:
                    break
                name = self.part['name']
                if Path(name).name != name:
                    raise ValueError('Unsafe part filename')
                self.current_path = (self.acquire(self.part) if self.acquire
                                     else self.directory / name)
                self.current = Path(self.current_path).open('rb')
                self.part_hash = hashlib.sha256()
                self.part_size = 0
            block = self.current.read(size - len(output))
            if block:
                output.extend(block)
                self.archive_hash.update(block)
                self.part_hash.update(block)
                self.part_size += len(block)
            else:
                self.current.close()
                self.current = None
                if (self.part_size != self.part['bytes'] or
                        self.part_hash.hexdigest() != self.part['sha256']):
                    raise ValueError('Part size/hash mismatch: ' + self.part['name'])
                if self.release:
                    self.release(self.current_path)
        return bytes(output)

    def close(self):
        if self.current is not None:
            self.current.close()
        super().close()


def restore(manifest_path, out=None, *, acquire=None, release=None):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    expected = {row['path']: row for row in manifest['files']}
    if len(expected) != len(manifest['files']):
        raise ValueError('Duplicate manifest member')
    out = Path(out) if out is not None else None
    if out is not None:
        if out.exists():
            raise FileExistsError('Use a new output directory')
        out.mkdir(parents=True)
    seen = set()
    with PartsReader(manifest, manifest_path.parent, acquire, release) as source:
        with tarfile.open(fileobj=source, mode='r|gz') as archive:
            for member in archive:
                name = member.name
                path = PurePosixPath(name)
                if (path.is_absolute() or '..' in path.parts or '\\' in name or
                        not member.isfile() or name in seen or name not in expected):
                    raise ValueError('Unsafe, duplicate or unexpected archive member: ' + name)
                seen.add(name)
                row = expected[name]
                if member.size != row['export_bytes']:
                    raise ValueError('Member size mismatch: ' + name)
                target = out / name if out is not None else None
                if target is not None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                output = target.open('xb') if target is not None else None
                digest, size = hashlib.sha256(), 0
                try:
                    with archive.extractfile(member) as stream:
                        for block in iter(lambda: stream.read(1024 * 1024), b''):
                            digest.update(block)
                            size += len(block)
                            if output is not None:
                                output.write(block)
                finally:
                    if output is not None:
                        output.close()
                if size != row['export_bytes'] or digest.hexdigest() != row['export_sha256']:
                    raise ValueError('Member hash mismatch: ' + name)
                if target is not None:
                    target.chmod(member.mode & 0o777)
        # Include gzip trailers/padding and finish checking every part.
        while source.read(1024 * 1024):
            pass
        if source.archive_hash.hexdigest() != manifest['archive_sha256']:
            raise ValueError('Archive hash mismatch')
    if seen != set(expected):
        raise ValueError('Archive and file inventory differ')
    return {'passed': True, 'files': len(seen), 'archive_sha256': manifest['archive_sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.out is None and not args.verify_only:
        parser.error('--out or --verify-only is required')
    print(json.dumps(restore(args.manifest, None if args.verify_only else args.out), indent=2))


if __name__ == '__main__':
    main()
