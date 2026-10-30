"""Recorder checks use temporary fixtures, never study run records."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'tools/run_case.py'


class RecorderTests(unittest.TestCase):
    def run_fixture(self, code, timeout=5, run_kind=None):
        with tempfile.TemporaryDirectory(prefix='smoke-recorder-') as tmp:
            base = Path(tmp)
            (base/'tools').mkdir(); (base/'configs').mkdir(); (base/'recipes').mkdir()
            shutil.copy2(RUNNER, base/'tools/run_case.py')
            (base/'configs/cases.json').write_text(json.dumps([{'suite':'fixture','id':'fixture','nodes':['halo']}]))
            p = subprocess.run([sys.executable, str(base/'tools/run_case.py'), '--private-root', str(base/'private'),
                                '--node', 'halo', '--suite', 'fixture', '--case', 'fixture', '--backend', 'cpu',
                                '--timeout', str(timeout),
                                *(['--run-kind', run_kind] if run_kind else []),
                                '--', sys.executable, '-c', code],
                               capture_output=True, text=True, timeout=timeout+8)
            result = json.loads(next((base/'private/results/runs').glob('*/*/result.json')).read_text())
            private = next((base/'private/runs').glob('*/*/execution.json'))
            return p, result, private.read_text()

    def test_exit_zero_and_valid_marker_still_need_review(self):
        p, r, private = self.run_fixture('print(\'SMOKE_RESULT_JSON:{"backend_observed":"cpu","physics_valid":true,"device":"/secret/host","metrics":{"error":0.0}}\')')
        self.assertEqual(p.returncode, 0)
        self.assertEqual(r['status'], 'PENDING_VALIDATION')
        self.assertFalse(r['validation']['reviewed'])
        self.assertNotIn('/secret/host', json.dumps(r))
        self.assertIn('/secret/host', private)

    def test_no_marker_is_pending(self):
        _, r, _ = self.run_fixture('print("finished")')
        self.assertEqual(r['status'], 'PENDING_VALIDATION')
        self.assertIsNone(r['backend_observed'])

    def test_non_cmake_build_is_explicit_and_does_not_establish_physics(self):
        _, r, _ = self.run_fixture('print("build completed")', run_kind='build')
        self.assertEqual(r['run_kind'], 'build')
        self.assertEqual(r['status'], 'PENDING_VALIDATION')
        self.assertIsNone(r['validation']['g1'])

    @unittest.skipIf(os.name=='nt','Recorder process-group termination requires Linux; exercised in CI')
    def test_timeout_stops_child(self):
        p, r, _ = self.run_fixture('import time; time.sleep(60)', timeout=1)
        self.assertEqual(p.returncode, 2)
        self.assertTrue(r['timed_out'])
        self.assertEqual(r['exit_code'], 124)
        self.assertEqual(r['status'], 'FAIL')
        self.assertLess(r['elapsed_wall_s'], 5)

    def test_authorized_extended_budget_recorded_without_auto_pass(self):
        p, r, _ = self.run_fixture('print("bounded fixture completed")', timeout=900)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(r['timeout_budget_s'], 900)
        self.assertEqual(r['status'], 'PENDING_VALIDATION')

    def test_long_preparation_budget_remains_unvalidated_nonphysics(self):
        p, r, _ = self.run_fixture('print("download metadata fixture")', timeout=7200, run_kind='preflight')
        self.assertEqual(p.returncode, 0)
        self.assertEqual(r['timeout_budget_s'], 7200)
        self.assertEqual(r['run_kind'], 'preflight')
        self.assertIsNone(r['validation']['g1'])
        self.assertFalse(r['validation']['reviewed'])
        self.assertEqual(r['status'], 'PENDING_VALIDATION')


if __name__ == '__main__':
    unittest.main()
