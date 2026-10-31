import unittest

from chaos_monkey.wrapper import ChaosTools, Fault

TOOLS = {"a": lambda: '{"n": 1}', "b": lambda: '{"n": 2}'}


class WrapperTests(unittest.TestCase):
    def test_passthrough_without_fault(self):
        t = ChaosTools(TOOLS)
        self.assertEqual(t["a"](), '{"n": 1}')
        self.assertEqual(t.injected, 0)

    def test_one_shot_hits_first_call_of_target_only(self):
        t = ChaosTools(TOOLS, Fault("a", "error"))
        self.assertEqual(t["b"](), '{"n": 2}')
        self.assertTrue(t["a"]().startswith("ERROR"))
        self.assertEqual(t["a"](), '{"n": 1}')
        self.assertEqual(t.injected, 1)

    def test_persistent_hits_every_call(self):
        t = ChaosTools(TOOLS, Fault("a", "empty", persistent=True))
        self.assertEqual((t["a"](), t["a"]()), ("", ""))
        self.assertEqual(t.injected, 2)

    def test_timeout_raises(self):
        with self.assertRaises(TimeoutError):
            ChaosTools(TOOLS, Fault("a", "timeout"))["a"]()

    def test_unknown_kind_and_tool(self):
        with self.assertRaises(ValueError):
            ChaosTools(TOOLS, Fault("a", "nope"))
        with self.assertRaises(KeyError):
            ChaosTools(TOOLS)["zzz"]

    def test_same_seed_same_corruption(self):
        f = Fault("a", "corrupted")
        self.assertEqual(ChaosTools(TOOLS, f, 3)["a"](), ChaosTools(TOOLS, f, 3)["a"]())
