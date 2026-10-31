"""Keep previously published handoffs verifiable after moving the study folders."""
import hashlib
import unittest

from replication.continue_stata import verify_catalogue_binding
from replication.paths import ROOT, repository_path


class HistoricalBindingTests(unittest.TestCase):
    def setUp(self):
        self.current = 'study/screening/review/inputs/catalogue.json'
        self.historical = 'step-2-twelve-trial-pilot/inputs/catalogue.json'
        self.digest = hashlib.sha256((ROOT / self.current).read_bytes()).hexdigest()

    def test_old_and_current_handoffs_bind_the_same_catalogue(self):
        for name in [self.historical, self.current]:
            with self.subTest(name=name):
                self.assertEqual(repository_path(name), ROOT / self.current)
                verify_catalogue_binding('REPOSITORY_ROOT/' + name, self.digest)

    def test_alias_does_not_admit_a_changed_hash_or_another_file(self):
        for name, digest in [(self.historical, '0' * 64),
                             ('step-2-twelve-trial-pilot/README.md', self.digest)]:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'binding changed'):
                verify_catalogue_binding('REPOSITORY_ROOT/' + name, digest)

    def test_historical_binding_cannot_escape_the_repository(self):
        for name in ['../catalogue.json', '/catalogue.json', 'study/../catalogue.json']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'relative POSIX'):
                verify_catalogue_binding('REPOSITORY_ROOT/' + name, self.digest)


if __name__ == '__main__':
    unittest.main()
