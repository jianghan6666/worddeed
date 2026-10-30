import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from replication.download import download, REPO


class DownloadTests(unittest.TestCase):
    def test_slow_connection_retries_a_new_url_and_preserves_full_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);urls=[]
            listing={'assets':[{'name':'asset','apiUrl':f'https://api.github.com/repos/{REPO}/releases/assets/1'}]}
            def fetched(cmd,**kwargs):
                urls.append(cmd[-1])
                path=Path(cmd[cmd.index('--output')+1])
                if len(urls)==1:
                    path.write_bytes(b'incomplete')
                    raise subprocess.CalledProcessError(28,cmd)
                path.write_bytes(b'complete')
            with patch('replication.download.subprocess.check_output',side_effect=[json.dumps(listing),'fixture-token']), \
                 patch('replication.download.subprocess.run',side_effect=fetched):
                download('gh','asset',root,'curl',True)
            self.assertEqual(len(urls),2)
            self.assertNotEqual(urls[0],urls[1])
            self.assertEqual((root/'asset').read_bytes(),b'complete')

    def test_interrupted_transfer_does_not_leave_final_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def failed(cmd,**kwargs):
                Path(cmd[-1],'asset').write_bytes(b'incomplete')
                raise subprocess.CalledProcessError(1,cmd)
            with patch('replication.download.subprocess.run',side_effect=failed):
                with self.assertRaises(subprocess.CalledProcessError):
                    download('gh','asset',root)
            self.assertFalse((root/'asset').exists())
            self.assertEqual(list(root.iterdir()),[])

    def test_http1_transport_keeps_credentials_off_command_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            listing={'assets':[{'name':'asset','apiUrl':f'https://api.github.com/repos/{REPO}/releases/assets/1'}]}
            def fetched(cmd,**kwargs):
                self.assertNotIn('fixture-token',' '.join(cmd))
                self.assertIn('Bearer fixture-token',kwargs['input'])
                Path(cmd[cmd.index('--output')+1]).write_bytes(b'complete')
            with patch('replication.download.subprocess.check_output',side_effect=[json.dumps(listing),'fixture-token\n']), \
                 patch('replication.download.subprocess.run',side_effect=fetched):
                download('gh','asset',root,'curl')
            self.assertEqual((root/'asset').read_bytes(),b'complete')
            self.assertEqual(list(root.iterdir()),[root/'asset'])
