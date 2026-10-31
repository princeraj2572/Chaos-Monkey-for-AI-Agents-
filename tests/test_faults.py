import json
import random
import unittest

from chaos_monkey.faults import FAULTS, KINDS


class FaultTests(unittest.TestCase):
    OUT = '{"a": 5, "b": ["x"], "c": 7}'

    def test_kinds(self):
        self.assertEqual(set(KINDS), {"empty", "error", "timeout", "truncated", "corrupted", "injection"})

    def test_empty_and_error(self):
        self.assertEqual(FAULTS["empty"](self.OUT, random.Random(0)), "")
        self.assertTrue(FAULTS["error"](self.OUT, random.Random(0)).startswith("ERROR"))

    def test_timeout_raises(self):
        with self.assertRaises(TimeoutError):
            FAULTS["timeout"](self.OUT, random.Random(0))

    def test_truncated_is_invalid_json(self):
        out = FAULTS["truncated"](self.OUT, random.Random(0))
        self.assertLess(len(out), len(self.OUT))
        with self.assertRaises(ValueError):
            json.loads(out)

    def test_injection_uses_only_pineapple(self):
        out = FAULTS["injection"](self.OUT, random.Random(0))
        self.assertTrue(out.startswith(self.OUT))
        self.assertIn("PINEAPPLE", out)

    def test_corrupted_changes_ints_only(self):
        out = json.loads(FAULTS["corrupted"](self.OUT, random.Random(0)))
        self.assertNotEqual(out["a"], 5)
        self.assertNotEqual(out["c"], 7)
        self.assertEqual(out["b"], ["x"])

    def test_corrupted_deterministic_and_passes_non_json(self):
        a = FAULTS["corrupted"](self.OUT, random.Random("s"))
        self.assertEqual(a, FAULTS["corrupted"](self.OUT, random.Random("s")))
        self.assertEqual(FAULTS["corrupted"]("not json", random.Random(0)), "not json")


if __name__ == "__main__":
    unittest.main()
