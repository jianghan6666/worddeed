"""Export a completed run for private review, with portable paths and no license headers."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replication.download import digest
from replication.restore import restore

TEXT = {'.json','.jsonl','.log','.txt','.csv','.tsv','.md','.html','.do'}
LICENSE_LOGS = {'launcher.log','run_models.log','run_models_stata18.log'}
PART_BYTES = 64 * 1024 * 1024


class PartWriter:
    """Write one gzip stream directly to bounded transport parts."""
    def __init__(self, out):
        self.out, self.parts = out, []
        self.stream = None
        self.total = 0
        self.archive_hash = hashlib.sha256()

    def write(self, data):
        size = len(data)
        self.archive_hash.update(data)
        self.total += size
        while data:
            if self.stream is None:
                self.name = f'fresh-reproduction.tar.gz.part{len(self.parts)+1:03d}'
                self.stream = (self.out/self.name).open('xb')
                self.count, self.part_hash = 0, hashlib.sha256()
            block, data = data[:PART_BYTES-self.count], data[PART_BYTES-self.count:]
            self.stream.write(block)
            self.part_hash.update(block)
            self.count += len(block)
            if self.count == PART_BYTES:
                self.finish_part()
        return size

    def tell(self):
        return self.total

    def flush(self):
        if self.stream is not None:
            self.stream.flush()

    def finish_part(self):
        if self.stream is not None:
            self.stream.close()
            self.parts.append({'name':self.name,'bytes':self.count,'sha256':self.part_hash.hexdigest()})
            self.stream = None


def package_run(run, out):
    supplied_run = str(Path(run).absolute())
    run, out = Path(run).resolve(), Path(out).resolve()
    completion = json.loads((run/'REPRODUCTION.json').read_text())
    if completion['status'] != 'complete':
        raise ValueError('Only a completed empirical run can be packaged')
    if out.exists():
        raise FileExistsError('Use a new export directory')
    out.mkdir(parents=True)
    config = json.loads((run/'reproduce.json').read_text())
    replacements = {str(run):'REPRODUCTION_ROOT',supplied_run:'REPRODUCTION_ROOT',str(ROOT):'REPOSITORY_ROOT',
                    config['python']:'PYTHON_EXECUTABLE',str(Path(sys.base_prefix).resolve()):'PYTHON_BASE_ENVIRONMENT'}
    python = Path(config['python'])
    if python.parent.name in {'bin','Scripts'}:
        replacements[str(python.parent.parent)]='ANALYSIS_ENVIRONMENT'
    if config.get('stata_exe'):
        replacements[config['stata_exe']]='STATA_EXECUTABLE'
    replacements=sorted(replacements.items(),key=lambda x:len(x[0]),reverse=True)
    paths = [p for p in run.iterdir() if p.is_file() and p.suffix=='.json']
    for folder in ['screening','workflow','supplementary','logs','diagnostics','windows']:
        paths += [p for p in (run/folder).rglob('*') if p.is_file()]
    writer = PartWriter(out)
    files, omissions = [], []
    with gzip.GzipFile(filename='', mode='wb', fileobj=writer, mtime=0) as compressed, \
         tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as tar:
        for path in sorted(paths):
            name = path.relative_to(run).as_posix()
            if path.name.lower() in LICENSE_LOGS:
                omissions.append({'path':name,'reason':'Raw Stata launch/batch header may contain local license details'})
                continue
            original_hash = digest(path)
            changed = False
            if path.suffix.lower() in TEXT:
                data = path.read_bytes()
                for source,target in replacements:
                    data=data.replace(source.encode(),target.encode())
                changed = hashlib.sha256(data).hexdigest()!=original_hash
                # Any remaining local user path needs inspection before export.
                if b'/Users/' in data or b'/home/' in data:
                    raise ValueError('Unnormalized local path requires review: '+name)
                size=len(data); export_hash=hashlib.sha256(data).hexdigest()
                stream=io.BytesIO(data)
            else:
                size=path.stat().st_size;export_hash=original_hash
                stream=path.open('rb')
            info=tarfile.TarInfo(name)
            info.size=size;info.mode=0o644;info.mtime=0
            with stream:
                tar.addfile(info,stream)
            files.append({'path':name,'original_bytes':path.stat().st_size,
                          'original_sha256':original_hash,'export_bytes':size,
                          'export_sha256':export_hash,
                          'transformations':['portable_local_paths'] if changed else []})
    writer.finish_part()
    parts=writer.parts
    manifest={'bundle':'fresh-reproduction','format':'concatenated gzip tar parts',
              'archive_sha256':writer.archive_hash.hexdigest(),'parts':parts,'files':files,'omissions':omissions,
              'scope':'New empirical run outputs; supplied inputs are in the separate frozen release bundles',
              'path_note':'Review export uses portable path tokens; resume the original local run or start a fresh reproduction. Numerical and binary scientific outputs are unchanged.'}
    destination=out/'fresh-reproduction.manifest.json'
    destination.write_text(json.dumps(manifest,indent=2)+'\n')
    result=restore(destination)
    return {**result,'parts':len(parts),'omitted_license_logs':len(omissions)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(package_run(args.run,args.out),indent=2))


if __name__=='__main__':
    main()
