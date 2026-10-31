"""The agent loop: drive a model (a generator of actions) against a tools mapping."""
from dataclasses import dataclass


@dataclass
class RunResult:
    final: str
    trace: list
    exhausted: bool = False


def run_agent(task, model, tools, max_steps=12):
    """model.start(task) yields {"tool","args"} or {"final"}; each tool result is sent back."""
    gen = model.start(task)
    trace = []
    try:
        action = next(gen)
        for _ in range(max_steps):
            if "final" in action:
                return RunResult(str(action["final"]), trace)
            name, args = action.get("tool"), action.get("args") or {}
            try:
                out = str(tools[name](**args))
            except Exception as e:  # a crashing tool is data for the agent, not for us
                out = f"ERROR: {type(e).__name__}"
            trace.append({"tool": name, "args": args, "result": out})
            action = gen.send(out)
    except StopIteration:
        pass
    return RunResult("", trace, True)
