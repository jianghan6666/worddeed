import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from replication.restore import restore


class RestoreTests(unittest.TestCase):
    def bundle(self, root, name='data/value.txt', payload=b'example', kind=None):
        raw=io.BytesIO()
        with tarfile.open(fileobj=raw,mode='w') as tar:
            info=tarfile.TarInfo(name)
            info.size=len(payload)
            if kind:
                info.type=kind
                info.linkname='../outside'
                info.size=0
            tar.addfile(info,None if kind else io.BytesIO(payload))
        data=gzip.compress(raw.getvalue())
        parts=[]
        for i,start in enumerate(range(0,len(data),17)):
            block=data[start:start+17]
            filename=f'archive.part{i:03d}'
            (root/filename).write_bytes(block)
            parts.append({'name':filename,'bytes':len(block),'sha256':hashlib.sha256(block).hexdigest()})
        spec={'parts':parts,'archive_sha256':hashlib.sha256(data).hexdigest(),
              'files':[{'path':name,'export_bytes':len(payload),'export_sha256':hashlib.sha256(payload).hexdigest()}]}
        path=root/'manifest.json';path.write_text(json.dumps(spec))
        return path,spec

    def test_stream_restores_across_part_boundaries_and_verifies_without_extraction(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);manifest,_=self.bundle(root)
            self.assertTrue(restore(manifest)['passed'])
            self.assertTrue(restore(manifest,root/'out')['passed'])
            self.assertEqual((root/'out/data/value.txt').read_bytes(),b'example')
            with self.assertRaises(FileExistsError):restore(manifest,root/'out')

    def test_rejects_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);manifest,spec=self.bundle(root)
            spec['parts'][0]['sha256']='0'*64;manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'Part size/hash mismatch'):restore(manifest)

    def test_acquired_parts_are_released_only_after_hash_check(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);manifest,spec=self.bundle(root)
            acquired=[];released=[]
            def acquire(part):
                acquired.append(part['name'])
                return root/part['name']
            def release(path):
                released.append(path.name)
            self.assertTrue(restore(manifest,acquire=acquire,release=release)['passed'])
            self.assertEqual(acquired,[p['name'] for p in spec['parts']])
            self.assertEqual(released,acquired)
            spec['parts'][0]['sha256']='0'*64;manifest.write_text(json.dumps(spec))
            released.clear()
            with self.assertRaisesRegex(ValueError,'Part size/hash mismatch'):
                restore(manifest,acquire=acquire,release=release)
            self.assertEqual(released,[])

    def test_rejects_traversal_and_symlinks(self):
        for name,kind in [('../outside',None),('data/link',tarfile.SYMTYPE)]:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as t:
                root=Path(t);manifest,_=self.bundle(root,name=name,kind=kind)
                with self.assertRaisesRegex(ValueError,'Unsafe'):restore(manifest,root/'out')
                self.assertFalse((root/'outside').exists())

    def test_rejects_truncated_inventory(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);manifest,spec=self.bundle(root)
            spec['files'].append({'path':'missing','export_bytes':0,'export_sha256':hashlib.sha256(b'').hexdigest()})
            manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'inventory differ'):restore(manifest)


if __name__=='__main__':unittest.main()
