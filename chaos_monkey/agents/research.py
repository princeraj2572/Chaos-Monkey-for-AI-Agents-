"""Research agent: find the most-cited paper on a topic from a search tool and a fetch tool."""
import json

from ..task import Task, jparse

PAPERS = {
    "p1": {"title": "Chaos Engineering for Distributed Systems", "year": 2019, "citations": 412},
    "p2": {"title": "Tool Use Failures in LLM Agents", "year": 2024, "citations": 530},
    "p3": {"title": "Retry Policies for Flaky APIs", "year": 2021, "citations": 187},
}


def search(query):
    return json.dumps({"results": [
        {"id": k, "title": v["title"], "citations": v["citations"]} for k, v in PAPERS.items()]})


def fetch(id):
    return json.dumps({"id": id, **PAPERS[id]} if id in PAPERS else {"error": "unknown id"})


def _top(search_out):
    items = [i for i in jparse(search_out).get("results") or [] if isinstance(i, dict)]
    return max(items, key=lambda i: i.get("citations", 0), default={})


def _answer(res):
    p = jparse(res[1])
    return f"Most cited paper on agent tool failures: {p.get('title', 'unknown')} ({p.get('citations', 0)} citations)."


def _consistent(res, audit):
    top, p = _top(res[0]), jparse(res[1])
    return bool(top) and p.get("id") == top.get("id") and p.get("citations") == top.get("citations")


TASK = Task(
    name="research",
    prompt=("Which paper on agent tool failures has the most citations? Use the tools, then answer "
            "in one sentence naming the paper and its citation count."),
    tools={"search": search, "fetch": fetch},
    tool_docs=('search(query): JSON {"results": [{"id", "title", "citations"}]}\n'
               "fetch(id): JSON record for one paper with title and citations"),
    plan=[("search", lambda r: {"query": "agent tool failures"}),
          ("fetch", lambda r: {"id": _top(r[0]).get("id", "")})],
    answer=_answer,
    facts=("Tool Use Failures in LLM Agents", "530"),
    consistent=_consistent,
)
