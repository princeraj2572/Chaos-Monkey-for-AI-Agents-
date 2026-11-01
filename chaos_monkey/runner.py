"""Run a task once clean, then once per sampled fault, and judge each run."""
import random

from .agent import run_agent
from .faults import KINDS
from .judge import OUTCOMES, is_correct, judge
from .wrapper import ChaosTools, Fault


def fault_space(task, kinds=KINDS):
    bad = [k for k in kinds if k not in KINDS]
    if bad:
        raise ValueError(f"unknown fault kind(s): {', '.join(bad)}; choose from {', '.join(KINDS)}")
    return [Fault(t, k, p) for t in task.tools for k in kinds for p in (False, True)]


def run_chaos(task, model, runs=None, seed=0, kinds=KINDS, on_run=None):
    """runs=None covers every fault once; otherwise `runs` seeded picks (cycling if > space).
    on_run(i, total, row) is called after each run, for live progress."""
    base = run_agent(task, model, ChaosTools(task.tools))
    space = fault_space(task, kinds)
    random.Random(seed).shuffle(space)
    rows = []
    total = len(space) if runs is None else runs
    for i in range(total):
        fault = space[i % len(space)]
        tools = ChaosTools(task.tools, fault, seed)
        r = run_agent(task, model, tools)
        rows.append({
            "fault": fault.label(), "tool": fault.tool, "kind": fault.kind,
            "persistent": fault.persistent,
            "outcome": judge(task, r.final, tools.injected, len(r.trace) > len(base.trace)),
            "final": r.final, "trace": r.trace,
        })
        if on_run:
            on_run(i + 1, total, rows[-1])
    counts = {o: sum(r["outcome"] == o for r in rows) for o in OUTCOMES}
    return {
        "agent": task.name, "model": model.name, "seed": seed,
        "baseline": {"final": base.final, "correct": is_correct(task, base.final), "calls": len(base.trace)},
        "counts": counts, "runs": rows,
    }
