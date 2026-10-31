"""Run a task once clean, then once per sampled fault, and judge each run."""
import random

from .agent import run_agent
from .faults import KINDS
from .judge import OUTCOMES, is_correct, judge
from .wrapper import ChaosTools, Fault


def fault_space(task):
    return [Fault(t, k, p) for t in task.tools for k in KINDS for p in (False, True)]


def run_chaos(task, model, runs=None, seed=0):
    """runs=None covers every fault once; otherwise `runs` seeded picks (cycling if > space)."""
    base = run_agent(task, model, ChaosTools(task.tools))
    space = fault_space(task)
    random.Random(seed).shuffle(space)
    rows = []
    for i in range(len(space) if runs is None else runs):
        fault = space[i % len(space)]
        tools = ChaosTools(task.tools, fault, seed)
        r = run_agent(task, model, tools)
        rows.append({
            "fault": fault.label(), "tool": fault.tool, "kind": fault.kind,
            "persistent": fault.persistent,
            "outcome": judge(task, r.final, tools.injected, len(r.trace) > len(base.trace)),
            "final": r.final, "trace": r.trace,
        })
    counts = {o: sum(r["outcome"] == o for r in rows) for o in OUTCOMES}
    return {
        "agent": task.name, "model": model.name, "seed": seed,
        "baseline": {"final": base.final, "correct": is_correct(task, base.final), "calls": len(base.trace)},
        "counts": counts, "runs": rows,
    }
