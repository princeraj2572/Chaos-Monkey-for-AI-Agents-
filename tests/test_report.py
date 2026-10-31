import json
import os
import tempfile
import unittest

from chaos_monkey.judge import OUTCOMES
from chaos_monkey.mock import MockCareful, MockNaive
from chaos_monkey.report import render_html, render_json, render_text, silent_rate, write_reports
from chaos_monkey.runner import run_chaos
from tests.toy import TOY


def results():
    return [run_chaos(TOY, m, seed=1) for m in (MockNaive(), MockCareful())]


class ReportTests(unittest.TestCase):
    def test_silent_rate_naive_above_careful(self):
        naive, careful = results()
        self.assertGreater(silent_rate(naive), 0)
        self.assertEqual(silent_rate(careful), 0)

    def test_text_names_models_and_mock_note(self):
        text = render_text(results())
        self.assertIn("toy / mock-naive", text)
        self.assertIn("silent-failure rate", text)
        self.assertIn("not language models", text)

    def test_json_roundtrips(self):
        self.assertEqual(json.loads(render_json(results()))[0]["model"], "mock-naive")

    def test_html_lists_every_outcome_and_escapes(self):
        rs = results()
        rs[0]["runs"][0]["final"] = "<script>alert(1)</script>"
        page = render_html(rs)
        for o in OUTCOMES:
            self.assertIn(o, page)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;", page)

    def test_no_mock_note_for_real_models(self):
        rs = results()
        for r in rs:
            r["model"] = "openai:x"
        self.assertNotIn("scripted stand-ins", render_html(rs))

    def test_write_reports(self):
        with tempfile.TemporaryDirectory() as d:
            paths = write_reports(results(), os.path.join(d, "nested"))
            self.assertTrue(all(os.path.getsize(p) > 0 for p in paths.values()))
