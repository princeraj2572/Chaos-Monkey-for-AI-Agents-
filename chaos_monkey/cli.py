"""chaos CLI: `run` one model, or `compare` several, over the example agents."""
import argparse
import sys

from .agents import AGENTS
from .models import make_model
from .report import render_text, write_reports
from .runner import run_chaos


def main(argv=None):
    p = argparse.ArgumentParser(prog="chaos", description="Chaos engineering for AI agents.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, help_ in (("run", "run one model"), ("compare", "run several models side by side")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("agents", nargs="*", help=f"any of: {', '.join(AGENTS)} (default: all)")
        s.add_argument("--runs", type=int, help="chaos runs per agent and model (default: every fault once)")
        s.add_argument("--seed", type=int, default=0)
        s.add_argument("--out", default="out", help="report directory")
        if name == "run":
            s.add_argument("--model", default="mock-naive")
        else:
            s.add_argument("--models", default="mock-naive,mock-careful", help="comma-separated")
    a = p.parse_args(argv)
    names = a.agents or list(AGENTS)
    specs = [a.model] if a.cmd == "run" else a.models.split(",")
    try:
        unknown = [n for n in names if n not in AGENTS]
        if unknown:
            raise ValueError(f"unknown agent(s): {', '.join(unknown)}")
        models = [make_model(s) for s in specs]
        results = [run_chaos(AGENTS[n], m, a.runs, a.seed) for n in names for m in models]
    except (ValueError, RuntimeError) as e:
        print(f"chaos: {e}", file=sys.stderr)
        return 2
    print(render_text(results))
    for path in write_reports(results, a.out).values():
        print(f"wrote {path}")
    return 0
