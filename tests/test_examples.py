import unittest

from chaos_monkey.agent import run_agent
from chaos_monkey.agents import AGENTS
from chaos_monkey.judge import is_correct
from chaos_monkey.mock import MockCareful, MockNaive, MockRetry
from chaos_monkey.report import silent_rate
from chaos_monkey.runner import run_chaos
from chaos_monkey.wrapper import ChaosTools


class ExampleAgentTests(unittest.TestCase):
    def test_both_examples_registered(self):
        self.assertEqual(set(AGENTS), {"research", "inventory"})

    def test_clean_runs_are_correct_for_both_mocks(self):
        for name, task in AGENTS.items():
            for model in (MockNaive(), MockCareful()):
                with self.subTest(agent=name, model=model.name):
                    self.assertTrue(is_correct(task, run_agent(task, model, ChaosTools(task.tools)).final))

    def test_naive_fails_silently_careful_recovers_or_flags(self):
        for name, task in AGENTS.items():
            with self.subTest(agent=name):
                naive = run_chaos(task, MockNaive(), seed=1)["counts"]
                careful = run_chaos(task, MockCareful(), seed=1)["counts"]
                self.assertGreater(naive["silent_failure"], 0)
                self.assertGreater(naive["hijacked"], 0)
                self.assertEqual(careful["silent_failure"] + careful["hijacked"], 0)
                self.assertGreater(careful["recovered"], 0)
                self.assertGreater(careful["flagged"], 0)

    def test_retry_sits_between_naive_and_careful(self):
        for name, task in AGENTS.items():
            with self.subTest(agent=name):
                rates = [silent_rate(run_chaos(task, m, seed=1)) for m in (MockNaive(), MockRetry(), MockCareful())]
                self.assertGreater(rates[0], rates[1])
                self.assertGreater(rates[1], rates[2])
