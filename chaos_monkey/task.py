"""A Task is an agent's job: prompt, tools, and what a correct answer looks like."""
import json
from dataclasses import dataclass
from typing import Callable, Optional


def jparse(text):
    """Parse a tool output into a dict; anything else becomes {}."""
    try:
        v = json.loads(text)
    except ValueError:
        return {}
    return v if isinstance(v, dict) else {}


@dataclass
class Task:
    name: str
    prompt: str
    tools: dict       # name -> callable(**args) -> str
    tool_docs: str    # shown to real models
    plan: list        # [(tool, fn(results_so_far) -> args)], used by scripted mocks
    answer: Callable  # fn(results) -> final answer text, used by scripted mocks
    facts: tuple      # substrings a correct answer must contain (case-insensitive)
    audit: Optional[tuple] = None  # (tool, args): extra call a careful agent uses to cross-check
    consistent: Callable = lambda results, audit: True
