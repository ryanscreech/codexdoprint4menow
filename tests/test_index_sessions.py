import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / 'skills/cad-continuity/scripts/index_sessions.py'
spec = importlib.util.spec_from_file_location('index_sessions', SCRIPT)
indexer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(indexer)


def event(kind, **payload):
    return {'type': kind, 'payload': payload}


class SessionIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, *events):
        path = self.root / name
        path.write_text(''.join(json.dumps(e) + '\n' for e in events), encoding='utf-8')
        return path

    def test_metadata_no_message_content_and_cumulative_usage_not_summed(self):
        path = self.write('one.jsonl', event('session_meta', id='one', cwd='/cad/part'),
                          event('event_msg', type='user_message', message='SECRET do evil things'),
                          *[event('event_msg', type='token_count', info={'total_token_usage': {
                              'input_tokens': n, 'cached_input_tokens': 20, 'output_tokens': 3,
                              'total_tokens': n + 3}}) for n in (100, 100, 150)])
        result = indexer.index_file(path, '/cad')
        self.assertTrue(result['parse_complete'])
        self.assertEqual(result['project_association'], 'cwd_match')
        self.assertEqual(result['sample_lines']['event_msg.user_message'], [2])
        self.assertEqual(result['last_reported_total_usage']['input_tokens'], 150)
        self.assertNotIn('SECRET', json.dumps(result))

    def test_identical_copies_only_deduplicated_and_forks_retained(self):
        first = self.write('a.jsonl', event('session_meta', id='one', cwd='/cad'))
        (self.root / 'b.jsonl').write_bytes(first.read_bytes())
        self.write('c.jsonl', event('session_meta', id='one', cwd='/cad'), event('compacted'))
        self.write('fork.jsonl', event('session_meta', id='fork', cwd='/cad', forked_from_id='one'))
        result = indexer.build_manifest([str(self.root), str(first)])
        self.assertEqual(result['files_indexed'], 4)
        self.assertEqual(sum('exact_duplicate_of' in r for r in result['sessions']), 1)
        self.assertEqual(sum(r.get('same_id_different_content', False) for r in result['sessions']), 3)
        self.assertFalse(result['semantic_audit_complete'])

    def test_malformed_lines_keep_physical_citations_and_fail_cli(self):
        path = self.write('bad.jsonl', event('session_meta', id='one'), [], event('event_msg', type='user_message'))
        with path.open('ab') as out:
            out.write(b'{"truncated":\n\xff\n')
        result = indexer.index_file(path)
        self.assertFalse(result['parse_complete'])
        self.assertEqual(result['sample_lines']['event_msg.user_message'], [3])
        self.assertEqual(result['issue_count'], 3)
        command = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
        self.assertEqual(command.returncode, 1)
        self.assertEqual(json.loads(command.stdout)['files_indexed'], 1)

    def test_windows_paths_are_case_insensitive_and_boundary_aware(self):
        self.assertEqual(indexer.association(['c:/CAD/Part/sub'], 'C:\\cad\\part'), 'cwd_match')
        self.assertEqual(indexer.association(['C:/CAD/Part2'], 'C:/CAD/Part'), 'needs_review')
        self.assertEqual(indexer.association(['/cad/Part'], '/cad/part'), 'needs_review')
        self.assertIsNone(indexer.recorded_path('/cad/../other'))

    def test_missing_archives_and_unknown_schemas_are_visible(self):
        self.write('unknown.jsonl', event('secret_unknown_event', password='SECRET'))
        (self.root / 'archive.jsonl.gz').write_bytes(b'not a supported archive')
        result = indexer.build_manifest([str(self.root), str(self.root / 'missing')])
        self.assertEqual(len(result['excluded']), 2)
        self.assertFalse(result['sessions'][0]['parse_complete'])
        self.assertNotIn('secret_unknown_event', json.dumps(result))

    def test_oversized_line_and_bounded_samples(self):
        path = self.write('big.jsonl', event('session_meta', id='one'),
                          event('response_item', type='message', content='X' * 200),
                          *[event('compacted') for _ in range(30)])
        with patch.object(indexer, 'MAX_LINE_BYTES', 100):
            result = indexer.index_file(path)
        self.assertEqual(result['lines'], 32)
        self.assertEqual(result['issues'][0], {'kind': 'oversized_line', 'line': 2})
        self.assertEqual(result['event_counts']['compacted'], 30)
        self.assertEqual(len(result['sample_lines']['compacted']), indexer.SAMPLE_LIMIT)
        import hashlib
        self.assertEqual(result['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_missing_usage_is_not_zero_and_turn_cwd_is_used(self):
        path = self.write('turn.jsonl', event('session_meta', id='one', cwd='/other'),
                          event('turn_context', cwd='/cad/part'),
                          event('event_msg', type='token_count', info=None))
        result = indexer.index_file(path, '/cad')
        self.assertEqual(result['project_association'], 'cwd_match')
        self.assertNotIn('last_reported_total_usage', result)

    def test_symlinks_are_not_followed(self):
        target = self.root / 'outside'
        target.mkdir()
        link = self.root / 'link'
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable on this platform/account')
        result = indexer.build_manifest([str(link)])
        self.assertEqual(result['files_indexed'], 0)
        self.assertEqual(result['excluded'][0]['reason'], 'symlink_not_followed')

    def test_utf8_bom_and_crlf(self):
        path = self.root / 'bom.jsonl'
        path.write_bytes(b'\xef\xbb\xbf' + json.dumps(event('session_meta', id='one')).encode() + b'\r\n')
        self.assertTrue(indexer.index_file(path)['parse_complete'])


if __name__ == '__main__':
    unittest.main()
