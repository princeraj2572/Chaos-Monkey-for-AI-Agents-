"""Wrap a task's tools so one chosen fault is injected into their outputs."""
import random
from dataclasses import dataclass

from .faults import FAULTS


@dataclass(frozen=True)
class Fault:
    tool: str
    kind: str
    persistent: bool = False  # False: first call only; True: every call

    def label(self):
        return f"{self.tool}:{self.kind}" + ("+persistent" if self.persistent else "")


class ChaosTools:
    """Dict-like view of the tools; at most one Fault is active. `injected` counts hits."""

    def __init__(self, tools, fault=None, seed=0):
        if fault and fault.kind not in FAULTS:
            raise ValueError(f"unknown fault kind: {fault.kind}")
        self._tools = tools
        self.fault = fault
        self.injected = 0
        self._rng = random.Random(f"{seed}|{fault.label() if fault else ''}")

    def __getitem__(self, name):
        fn = self._tools[name]

        def call(**args):
            out = fn(**args)
            f = self.fault
            if f and name == f.tool and (f.persistent or not self.injected):
                self.injected += 1
                return FAULTS[f.kind](out, self._rng)
            return out

        return call
