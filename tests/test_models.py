import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from chaos_monkey.agent import run_agent
from chaos_monkey.models import ChatModel, make_model, parse_action
from chaos_monkey.wrapper import ChaosTools
from tests.toy import TOY

KEY = "sk-test-secret-123"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def anthropic_reply(text):
    return FakeResponse(json.dumps({"content": [{"type": "text", "text": text}]}).encode())


def openai_reply(text):
    return FakeResponse(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


class ModelTests(unittest.TestCase):
    def setUp(self):
        p = mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": KEY, "OPENAI_API_KEY": KEY})
        p.start()
        self.addCleanup(p.stop)

    def test_parse_action(self):
        self.assertEqual(parse_action('ok {"tool": "get", "args": {}} bye')["tool"], "get")
        self.assertEqual(parse_action("plain words"), {"final": "plain words"})
        self.assertEqual(parse_action('{"other": 1}'), {"final": '{"other": 1}'})

    def test_anthropic_agent_loop_with_stubbed_urlopen(self):
        replies = [anthropic_reply('{"tool": "get", "args": {"k": "x"}}'), anthropic_reply('{"final": "n is 5"}')]
        with mock.patch("urllib.request.urlopen", side_effect=replies) as urlopen:
            r = run_agent(TOY, ChatModel("anthropic", "m1"), ChaosTools(TOY.tools))
        self.assertEqual(r.final, "n is 5")
        self.assertEqual(len(r.trace), 1)
        req = urlopen.call_args_list[0].args[0]
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.get_header("X-api-key"), KEY)
        second = json.loads(urlopen.call_args_list[1].args[0].data)
        self.assertIn("Tool result", second["messages"][-1]["content"])

    def test_openai_final_answer(self):
        with mock.patch("urllib.request.urlopen", side_effect=[openai_reply('{"final": "hi"}')]) as urlopen:
            r = run_agent(TOY, ChatModel("openai", "m2"), ChaosTools(TOY.tools))
        self.assertEqual(r.final, "hi")
        req = urlopen.call_args.args[0]
        self.assertEqual(req.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(req.get_header("Authorization"), f"Bearer {KEY}")

    def test_ollama_is_local_and_needs_no_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("urllib.request.urlopen", side_effect=[openai_reply('{"final": "ok"}')]) as urlopen:
                r = run_agent(TOY, make_model("ollama:llama3.2"), ChaosTools(TOY.tools))
        self.assertEqual(r.final, "ok")
        req = urlopen.call_args.args[0]
        self.assertTrue(req.full_url.startswith("http://127.0.0.1:11434/"))
        self.assertIsNone(req.get_header("Authorization"))

    def test_http_error_does_not_leak_key(self):
        err = urllib.error.HTTPError("https://x", 401, "bad", {}, io.BytesIO(KEY.encode()))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(RuntimeError) as cm:
                run_agent(TOY, ChatModel("openai", "m"), ChaosTools(TOY.tools))
        self.assertIn("401", str(cm.exception))
        self.assertNotIn(KEY, str(cm.exception))

    def test_network_errors_become_runtime_errors(self):
        for exc in (TimeoutError(), urllib.error.URLError("refused")):
            with self.subTest(exc=type(exc).__name__):
                with mock.patch("urllib.request.urlopen", side_effect=exc):
                    with self.assertRaises(RuntimeError) as cm:
                        run_agent(TOY, ChatModel("openai", "m"), ChaosTools(TOY.tools))
                self.assertIn("request failed", str(cm.exception))

    def test_factory(self):
        self.assertEqual(make_model("mock-naive").name, "mock-naive")
        self.assertEqual(make_model("mock-retry").name, "mock-retry")
        self.assertEqual(make_model("openai:gpt-x").name, "openai:gpt-x")
        with self.assertRaises(ValueError):
            make_model("llama")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                make_model("anthropic:m")
