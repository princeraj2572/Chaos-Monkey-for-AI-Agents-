"""A tiny Task for tests."""
import json

from chaos_monkey.task import Task, jparse

TOY = Task(
    name="toy",
    prompt="What is n?",
    tools={"get": lambda k: json.dumps({"k": k, "n": 5})},
    tool_docs="get(k): returns JSON with n",
    plan=[("get", lambda r: {"k": "x"})],
    answer=lambda res: f"n is {jparse(res[0]).get('n', 0)}",
    facts=("n is 5",),
    audit=("get", {"k": "x"}),
    consistent=lambda res, audit: jparse(res[0]) == jparse(audit),
)
