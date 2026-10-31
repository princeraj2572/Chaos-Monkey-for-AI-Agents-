import contextlib
import io
import json
import os
import tempfile
import unittest

from chaos_monkey.cli import main


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def read(d, name):
    with open(os.path.join(d, name), "rb") as f:
        return f.read()


class CliTests(unittest.TestCase):
    def test_compare_writes_reports_and_same_seed_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            code, out, _ = cli("compare", "--seed", "1", "--out", a)
            self.assertEqual(code, 0)
            self.assertIn("research / mock-naive", out)
            self.assertIn("inventory / mock-careful", out)
            self.assertIn("research / mock-retry", out)
            cli("compare", "--seed", "1", "--out", b)
            for name in ("report.json", "report.html"):
                self.assertEqual(read(a, name), read(b, name))
            cli("compare", "--seed", "2", "--out", b)
            self.assertNotEqual(read(a, "report.json"), read(b, "report.json"))

    def test_run_single_model_and_run_count(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, _ = cli("run", "research", "--model", "mock-careful", "--runs", "5", "--out", d)
            self.assertEqual(code, 0)
            data = json.loads(read(d, "report.json"))
            self.assertEqual([(r["agent"], r["model"], len(r["runs"])) for r in data],
                             [("research", "mock-careful", 5)])

    def test_kinds_option(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli("run", "research", "--kinds", "stale,empty", "--out", d)[0], 0)
            kinds = {x["kind"] for r in json.loads(read(d, "report.json")) for x in r["runs"]}
            self.assertEqual(kinds, {"stale", "empty"})

    def test_bad_agent_and_bad_model_exit_2_without_traceback(self):
        for argv in (("run", "nope"), ("run", "research", "--model", "llama"),
                     ("run", "research", "--kinds", "nope")):
            with self.subTest(argv=argv):
                code, _, err = cli(*argv)
                self.assertEqual(code, 2)
                self.assertTrue(err.startswith("chaos:"))
