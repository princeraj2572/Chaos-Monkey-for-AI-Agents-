import json
import unittest

from chaos_monkey.mock import MockCareful, MockNaive
from chaos_monkey.runner import fault_space, run_chaos
from tests.toy import TOY


class RunnerTests(unittest.TestCase):
    def test_space_covers_tools_kinds_and_persistence(self):
        self.assertEqual(len(fault_space(TOY)), 2 * 7 * 2)

    def test_naive_has_silent_failures_and_hijacks(self):
        r = run_chaos(TOY, MockNaive(), seed=1)
        self.assertGreater(r["counts"]["silent_failure"], 0)
        self.assertGreater(r["counts"]["hijacked"], 0)
        self.assertEqual(r["counts"]["not_injected"], 14)  # naive never calls "check"
        self.assertEqual(sum(r["counts"].values()), len(r["runs"]))

    def test_careful_never_fails_silently(self):
        r = run_chaos(TOY, MockCareful(), seed=1)
        self.assertEqual(r["counts"]["silent_failure"] + r["counts"]["hijacked"], 0)
        self.assertGreater(r["counts"]["recovered"], 0)
        self.assertGreater(r["counts"]["flagged"], 0)

    def test_runs_limits_and_cycles(self):
        self.assertEqual(len(run_chaos(TOY, MockNaive(), runs=5)["runs"]), 5)
        self.assertEqual(len(run_chaos(TOY, MockNaive(), runs=30)["runs"]), 30)

    def test_same_seed_is_byte_identical(self):
        dump = lambda s: json.dumps(run_chaos(TOY, MockNaive(), runs=10, seed=s), sort_keys=True)
        self.assertEqual(dump(7), dump(7))
        self.assertNotEqual(dump(7), dump(8))
