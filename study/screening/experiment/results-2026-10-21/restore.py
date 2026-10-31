#!/usr/bin/env python3
"""Restore the verified private evidence archive beside this file; no downloads."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    args=parser.parse_args()
    manifest=json.loads((HERE/'BUNDLE.json').read_text())
    if hashlib.sha256(args.archive.read_bytes()).hexdigest()!=manifest['sha256']:
        raise ValueError('Archive SHA-256 differs from the reviewed bundle')
    expected={x['path']:x for x in manifest['files']}
    with tarfile.open(args.archive,'r:gz') as archive:
        members=archive.getmembers()
        if len(members)!=len(expected) or {x.name for x in members}!=set(expected):
            raise ValueError('Archive member set mismatch')
        for member in members:
            rel=PurePosixPath(member.name)
            if not member.isfile() or rel.is_absolute() or '..' in rel.parts:
                raise ValueError('Unsafe archive member')
            destination=HERE.joinpath(*rel.parts)
            if not destination.resolve().is_relative_to(HERE) or any(p.is_symlink() for p in [destination,*destination.parents]):
                raise ValueError('Unsafe restore destination')
            payload=archive.extractfile(member).read()
            if hashlib.sha256(payload).hexdigest()!=expected[member.name]['sha256']:
                raise ValueError('Member SHA-256 mismatch')
            if destination.exists():
                if destination.read_bytes()!=payload:
                    raise ValueError('Refusing to overwrite a different local file: '+member.name)
            else:
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(payload)
    print(f'Restored/verified {len(expected)} private evidence files; existing differing files are never overwritten.')


if __name__=='__main__':
    main()
