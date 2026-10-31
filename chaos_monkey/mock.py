"""Scripted stand-ins for models (NOT language models), for reproducible demos.

mock-naive trusts every tool output. mock-retry retries bad output once and nothing more.
mock-careful validates outputs, retries once,
cross-checks sources, and flags what it cannot confirm.
"""
from .task import jparse

BAD_MARKERS = ("PINEAPPLE", "IGNORE PREVIOUS")


class MockNaive:
    name = "mock-naive"

    def start(self, task):
        res = []
        for tool, args in task.plan:
            out = yield {"tool": tool, "args": args(res)}
            if "PINEAPPLE" in out:  # obeys instructions found inside tool output
                yield {"final": "PINEAPPLE"}
                return
            res.append(out)
        yield {"final": task.answer(res)}


def _bad(out):
    return out.startswith("ERROR") or any(m in out for m in BAD_MARKERS) or not jparse(out)


def _call(tool, args):
    for _ in range(2):  # one retry
        out = yield {"tool": tool, "args": args}
        if not _bad(out):
            return out
    return None


class MockRetry:
    """Retries obviously bad output once, but never cross-checks and never flags."""
    name = "mock-retry"

    def start(self, task):
        res = []
        for tool, args in task.plan:
            out = yield from _call(tool, args(res))
            res.append(out or "")
        yield {"final": task.answer(res)}


class MockCareful:
    name = "mock-careful"

    def start(self, task):
        for _ in range(2):  # a second full pass if sources disagree
            res = []
            for tool, args in task.plan:
                out = yield from _call(tool, args(res))
                if out is None:
                    yield {"final": f"Unable to complete: {tool} gave unusable output twice; answer unverified."}
                    return
                res.append(out)
            audit = None
            if task.audit:
                audit = yield from _call(*task.audit)
                if audit is None:
                    yield {"final": "Unable to verify the data; answer unverified."}
                    return
            if task.consistent(res, audit):
                yield {"final": task.answer(res)}
                return
        yield {"final": "Unable to confirm: sources disagree, so this answer is unreliable."}
