import unittest

from chaos_monkey.agent import run_agent
from chaos_monkey.faults import KINDS
from chaos_monkey.mock import MockCareful, MockNaive
from chaos_monkey.wrapper import ChaosTools, Fault
from tests.toy import TOY


def run(model, kind=None, persistent=False):
    fault = Fault("get", kind, persistent) if kind else None
    return run_agent(TOY, model, ChaosTools(TOY.tools, fault))


class MockTests(unittest.TestCase):
    def test_naive_is_silently_wrong_on_empty(self):
        self.assertEqual(run(MockNaive(), "empty").final, "n is 0")

    def test_naive_obeys_injection(self):
        self.assertEqual(run(MockNaive(), "injection").final, "PINEAPPLE")

    def test_careful_clean_run_audits(self):
        r = run(MockCareful())
        self.assertEqual((r.final, len(r.trace)), ("n is 5", 2))

    def test_careful_recovers_from_one_shot_faults(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                r = run(MockCareful(), kind)
                self.assertEqual(r.final, "n is 5")
                self.assertGreater(len(r.trace), 2)

    def test_careful_flags_persistent_faults(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                final = run(MockCareful(), kind, persistent=True).final
                self.assertNotIn("n is 5", final)
                self.assertNotIn("PINEAPPLE", final)
                self.assertTrue(final.startswith("Unable"))
