"""Model factory plus real chat clients (anthropic:, openai:) over plain urllib."""
import json
import os
import re
import urllib.error
import urllib.request

from .mock import MockCareful, MockNaive, MockRetry

KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
SYSTEM = (
    "You are an agent that completes a task using tools. Reply with ONLY one JSON object per turn: "
    '{"tool": "<name>", "args": {...}} to call a tool, or {"final": "<answer>"} when done. '
    "Tool results arrive in the next message.\nTools:\n"
)


def parse_action(text):
    """First {...} block in the reply; if none parses, the whole reply is the final answer."""
    m = re.search(r"\{.*\}", text, re.S)
    try:
        v = json.loads(m.group(0)) if m else None
    except ValueError:
        v = None
    return v if isinstance(v, dict) and ("tool" in v or "final" in v) else {"final": text.strip()}


class ChatModel:
    def __init__(self, provider, model):
        self.provider, self.model, self.name = provider, model, f"{provider}:{model}"
        self._key = os.environ.get(KEY_ENV[provider])
        if not self._key:
            raise RuntimeError(f"{KEY_ENV[provider]} is not set")

    def _post(self, url, headers, body):
        req = urllib.request.Request(
            url, json.dumps(body).encode(), {"content-type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:  # report status only; never echo request details
            raise RuntimeError(f"{self.provider} API returned HTTP {e.code}") from None

    def _complete(self, system, messages):
        if self.provider == "anthropic":
            r = self._post("https://api.anthropic.com/v1/messages",
                           {"x-api-key": self._key, "anthropic-version": "2023-06-01"},
                           {"model": self.model, "max_tokens": 1024, "system": system, "messages": messages})
            return r["content"][0]["text"]
        r = self._post("https://api.openai.com/v1/chat/completions",
                       {"authorization": f"Bearer {self._key}"},
                       {"model": self.model, "messages": [{"role": "system", "content": system}] + messages})
        return r["choices"][0]["message"]["content"]

    def start(self, task):
        system = SYSTEM + task.tool_docs
        messages = [{"role": "user", "content": task.prompt}]
        while True:
            text = self._complete(system, messages)
            action = parse_action(text)
            if "final" in action:
                yield action
                return
            result = yield action
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"Tool result:\n{result}"}]


def make_model(spec):
    if spec == "mock-naive":
        return MockNaive()
    if spec == "mock-retry":
        return MockRetry()
    if spec == "mock-careful":
        return MockCareful()
    provider, _, model = spec.partition(":")
    if provider in KEY_ENV and model:
        return ChatModel(provider, model)
    raise ValueError(f"unknown model {spec!r}: use mock-naive, mock-retry, mock-careful, anthropic:<model> or openai:<model>")
