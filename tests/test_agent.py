import unittest

from chaos_monkey.agent import run_agent
from chaos_monkey.mock import MockNaive
from chaos_monkey.wrapper import ChaosTools
from tests.toy import TOY


class Forever:
    def start(self, task):
        while True:
            yield {"tool": "get", "args": {"k": "x"}}


class Bogus:
    def start(self, task):
        yield {"tool": "nope", "args": {}}
        yield {"final": "done"}


class AgentLoopTests(unittest.TestCase):
    def test_clean_run(self):
        r = run_agent(TOY, MockNaive(), ChaosTools(TOY.tools))
        self.assertEqual(r.final, "n is 5")
        self.assertEqual(len(r.trace), 1)
        self.assertFalse(r.exhausted)

    def test_step_limit(self):
        r = run_agent(TOY, Forever(), ChaosTools(TOY.tools), max_steps=3)
        self.assertTrue(r.exhausted)
        self.assertEqual(len(r.trace), 3)

    def test_unknown_tool_becomes_error_output(self):
        r = run_agent(TOY, Bogus(), ChaosTools(TOY.tools))
        self.assertEqual(r.trace[0]["result"], "ERROR: KeyError")
        self.assertEqual(r.final, "done")
