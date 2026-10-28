"""Synthetic offline packets exercise the frozen importer; no scientific judgments."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_system.empirical import screening


@unittest.skipUnless(os.environ.get('NBM_SCREENING_TOOLKIT'),
                     'Set NBM_SCREENING_TOOLKIT to the external frozen toolkit for screening checks')
class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.packets = self.root / 'runtime'
        self.out = self.root / 'run'
        self.toolkit = Path(os.environ['NBM_SCREENING_TOOLKIT']).resolve()
        self.tk = screening._load_toolkit(self.toolkit, self.packets)
        self.config = {'step2': {'toolkit': str(self.toolkit), 'packet_root': str(self.packets)}}
        self.calls = []
        self.bad = None
        self.make_packets()
        self.config['catalogue'] = str(self.packets / 'packets/catalogue.json')

    def make_packets(self):
        # Short invented descriptors/passages, retaining the frozen 354/18/1062 roster.
        tk = self.tk
        topics = [{'topic_id': str(i), 'name': 'Invented topic', 'keywords': ['invented']}
                  for i in range(354)]
        sources = [{'passage_id': f't{i}-r{n}', 'text': f'Invented passage {i} {n}.'}
                   for i in range(354) for n in (1, 2, 3)]
        tk.write(self.packets / 'packets/catalogue.json',
                 {'topic_model_id': 'synthetic-fixture', 'topics': topics})
        tk.write(self.packets / 'packets/source_packet.private.json', {'passages': sources})
        tk.write(self.packets / 'packets/schedule.json', {'jobs': [{'trial_id': 'historical'}]})
        for name in ['prompts/P0.md', 'initial_addendum.md', 'review_prompt.md',
                     'source_evidence.private.jsonl']:
            tk.textwrite(self.packets / 'packets' / name, 'Offline fixture only.\n')
        for review in (False, True):
            tk.write(self.packets / 'schemas' / ('review.schema.json' if review else 'initial.schema.json'),
                     tk.response_schema(review))
        initial_path = 'packets/stageA/P0.json'
        tk.write(self.packets / initial_path, {'topics': topics, 'prompt': 'Fixture P0',
                                              'stage': tk.INITIAL})
        pages = []
        for offset in range(0, 354, 20):
            page_id = f'B{len(pages) + 1:02}'
            path = f'packets/stageB/{page_id}.json'
            ids = [t['topic_id'] for t in topics[offset:offset + 20]]
            tk.write(self.packets / path, {'topic_ids': ids,
                     'passages': [p for p in sources if p['passage_id'].split('-')[0][1:] in ids]})
            pages.append({'page_id': page_id, 'topic_ids': ids, 'path': path,
                          'sha256': tk.sha(self.packets / path)})
        tk.write(self.packets / 'PACKET_MANIFEST.json', {
            'stageA': [{'prompt_id': 'P0', 'path': initial_path,
                        'sha256': tk.sha(self.packets / initial_path)}],
            'stageB': pages, 'file_hashes': {}, 'topic_model_id': 'synthetic-fixture',
            'catalogue_sha256': tk.sha(self.packets / 'packets/catalogue.json'),
            'source_packet_sha256': tk.sha(self.packets / 'packets/source_packet.private.json')})

    def row(self, slot, tid, review=False):
        label = 'relevant' if review and slot in 'AB' else 'irrelevant'
        row = {'topic_id': tid, 'status': 'resolved', 'label': label,
               'rationale': f'private-{slot}-reason-{tid}', 'evidence_keywords': ['invented'],
               'confidence_level': 'low' if slot in 'AB' else 'high',
               'confidence_reason': 'Fixture confidence only'}
        if review:
            row.update(reviewed_passage_ids=[f't{tid}-r{n}' for n in (1, 2, 3)],
                       evidence_passages=[{'passage_id': f't{tid}-r1',
                                           'excerpt': f'Invented passage {tid} 1.'}],
                       topic_interpretation_assessment='supported',
                       interpretation_reason='Fixture interpretation',
                       review_action='revised' if slot in 'AB' else 'retained',
                       change_reason='Fixture change reason')
        return row

    def factory(self, slot, model, effort):
        self.assertEqual((model, effort), ('gpt-6-astra', 'xhigh'))
        case = self

        class Provider:
            def respond(self, role, instructions, tools, history):
                case.assertEqual(role, slot)
                packet = json.loads(history[-1]['content'])
                review = packet['stage'] == case.tk.REVIEW
                page_id = packet.get('page_id')
                case.calls.append((slot, page_id))
                # Provider never receives other readers' reasons or receipt paths.
                serialized = json.dumps(history)
                for peer in set('ABC') - {slot}:
                    case.assertNotIn(f'private-{peer}-reason', serialized)
                case.assertNotIn('release_receipt', serialized)
                if review:
                    case.assertTrue(all((case.out / s / 'initial/sealed/seal.json').exists()
                                        for s in 'ABC'))
                    case.assertIn(f'private-{slot}-reason', serialized)
                    ids = packet['source_page']['topic_ids']
                    case.assertEqual(len(packet['source_page']['passages']), len(ids) * 3)
                else:
                    case.assertFalse((case.out / 'release.json').exists())
                    ids = [t['topic_id'] for t in packet['topics']]
                    case.assertEqual(len(ids), 354)
                rows = [case.row(slot, tid, review) for tid in ids]
                if case.bad == 'id' and not review:
                    rows[0]['topic_id'] = 'unknown'
                if case.bad == 'quote' and review:
                    rows[0]['evidence_passages'][0]['excerpt'] = 'Not source text'
                return {'id': f'fixture-{slot}-{page_id}', 'fixture': True,
                        'status': 'completed', 'model': 'synthetic-fixture',
                        'output': [{'type': 'function_call', 'name': 'submit_labels',
                                    'call_id': f'call-{slot}-{page_id}',
                                    'arguments': json.dumps({'labels': rows})}]}
        return Provider()

    def test_barrier_independence_resume_and_unweighted_majority(self):
        original = screening._exchange

        def interrupt_after_seal(*args, **kwargs):
            result = original(*args, **kwargs)
            if kwargs.get('page_id') == 'B01':
                raise RuntimeError('simulated process interruption after durable seal')
            return result

        with patch.object(screening, '_exchange', side_effect=interrupt_after_seal):
            with self.assertRaisesRegex(RuntimeError, 'process interruption'):
                screening.run(self.config, self.out, provider_factory=self.factory)
        self.assertEqual(self.calls, [('A', None), ('B', None), ('C', None), ('A', 'B01')])
        first = (self.out / 'A/B01/response.json').read_bytes()
        result = screening.run(self.config, self.out, provider_factory=self.factory)
        self.assertEqual(len(self.calls), 57)
        self.assertEqual((self.out / 'A/B01/response.json').read_bytes(), first)
        self.assertTrue(Path(result['selection']).is_absolute())
        selection = self.tk.loads(result['selection'])
        self.assertEqual(len(selection['selected_topic_ids']), 354)
        self.assertEqual(self.tk.loads(result['initial_selection'])['selected_topic_ids'], [])
        detail = self.tk.loads(result['reasons'])['topics'][0]
        self.assertEqual(detail['reviewed']['minority_slots'], [2])
        self.assertEqual(detail['readers']['C']['reviewed']['rationale'], 'private-C-reason-0')
        self.assertEqual(detail['reviewed']['votes'], ['relevant', 'relevant', 'irrelevant'])
        screening.run(self.config, self.out, provider_factory=self.factory)
        self.assertEqual(len(self.calls), 57)
        self.assertEqual(result['mode'], 'offline_fixture')
        changed = copy.deepcopy(self.config)
        changed['step2']['effort'] = 'high'
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            screening.run(changed, self.out, provider_factory=self.factory)
        Path(result['selection']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Binding mismatch'):
            screening.run(self.config, self.out, provider_factory=self.factory)

    def test_unknown_id_fails_preserves_first_response_without_retry(self):
        self.bad = 'id'
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, 'unknown_topic'):
                screening.run(self.config, self.out, provider_factory=self.factory)
        self.assertEqual(self.calls, [('A', None)])
        self.assertTrue((self.out / 'A/initial/literal-response.json').exists())
        self.assertFalse((self.out / 'release.json').exists())

    def test_exact_source_quotation_failure_stops_without_repair(self):
        self.bad = 'quote'
        with self.assertRaisesRegex(ValueError, 'quotation'):
            screening.run(self.config, self.out, provider_factory=self.factory)
        self.assertTrue((self.out / 'A/B01/literal-response.json').exists())
        self.assertFalse((self.out / 'A/B01/sealed').exists())
        self.assertEqual(len(self.calls), 4)

    def test_default_is_demo_and_historical_trial_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Demo only'):
            screening.run({}, self.out)
        self.config['step2']['trial_id'] = 'historical'
        with self.assertRaisesRegex(ValueError, 'historical trial IDs'):
            screening.run(self.config, self.out, provider_factory=self.factory)

    def test_frozen_validator_missing_votes_and_quote_membership(self):
        a, b, c = [self.row(slot, '0', True) for slot in 'ABC']
        self.assertEqual(self.tk.majority([a, b, c])['label'], 'relevant')
        self.assertIsNone(self.tk.majority([a, c, None])['label'])
        initial = {'labels': [self.row('A', '0')]}
        self.assertEqual(self.tk.validate([a], self.tk.REVIEW, ['0'], initial), [])
        bad = copy.deepcopy(a)
        bad['evidence_passages'][0]['excerpt'] = 'invented passage 0 1.'
        self.assertIn('quotation', [d['code'] for d in self.tk.validate([bad], self.tk.REVIEW, ['0'], initial)])
        bad = copy.deepcopy(a)
        bad['topic_id'] = 'unknown'
        self.assertIn('unknown_topic', [d['code'] for d in self.tk.validate([bad], self.tk.REVIEW, ['0'], initial)])

    def test_catalogue_hash_and_model_mismatch_fail_before_provider(self):
        path = self.root / 'stage1-catalogue.json'
        catalogue = self.tk.cat()
        catalogue['topic_model_id'] = 'different-model'
        self.tk.write(path, catalogue)
        self.config['catalogue'] = str(path)
        with self.assertRaisesRegex(ValueError, 'catalogue SHA/model identity'):
            screening.run(self.config, self.out, provider_factory=self.factory)
        # Matching bytes alone must not bypass the model identity check.
        manifest = self.tk.manifest()
        manifest['catalogue_sha256'] = self.tk.sha(path)
        self.tk.write(self.packets / 'PACKET_MANIFEST.json', manifest)
        with self.assertRaisesRegex(ValueError, 'catalogue SHA/model identity'):
            screening.run(self.config, self.out, provider_factory=self.factory)
        self.assertEqual(self.calls, [])
        self.assertFalse(self.out.exists())

    def test_rejects_incomplete_refused_malformed_and_reused_calls(self):
        call = {'type': 'function_call', 'name': 'submit_labels', 'call_id': 'first',
                'arguments': '{"labels":[]}'}
        valid = {'status': 'completed', 'output': [call]}
        for status in (None, 'incomplete', 'failed', 'in_progress'):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, 'did not complete'):
                screening._literal(dict(valid, status=status), [])
        with self.assertRaisesRegex(ValueError, 'did not complete'):
            screening._literal({'output': [call]}, [])
        refused = dict(valid, output=[call, {'type': 'message', 'content': [
            {'type': 'refusal', 'refusal': 'Fixture refusal'}]}])
        with self.assertRaisesRegex(ValueError, 'refused'):
            screening._literal(refused, [])
        with self.assertRaisesRegex(ValueError, 'Duplicate function call_id'):
            screening._literal(valid, [call])
        with self.assertRaisesRegex(ValueError, 'list of objects'):
            screening._literal(dict(valid, output=[None]), [])
        with self.assertRaisesRegex(ValueError, 'Incomplete output item'):
            screening._literal(dict(valid, output=[dict(call, status='incomplete')]), [])
        self.assertEqual(screening._literal(valid, [])[0], call['arguments'])


if __name__ == '__main__':
    unittest.main()
