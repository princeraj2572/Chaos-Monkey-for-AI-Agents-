# Chaos Monkey for AI Agents

**Chaos engineering for AI agents — break their tools on purpose and measure what they silently get wrong.**

AI agents lean on tools: search, databases, APIs. Tools fail all the time. They time out, return nothing, hand back half a response, or return numbers that are slightly off. The worst outcome is not a crash. It is an agent that carries on and delivers a confident, wrong answer.

This project is for developers who are about to trust an agent with real work. It wraps the agent's tools and injects exactly one fault per run: empty output, an error, a timeout, truncated output, corrupted numbers, stale numbers, or a hidden instruction (the harmless word PINEAPPLE). The agent is not told. A judge compares the final answer with a clean run and labels the result: recovered, flagged, silent failure, hijacked, unaffected, or not injected. You get a terminal summary, JSON, and an HTML report with a trace for every run.

Prompt testing asks how a model responds to different inputs. This changes what the world tells the agent mid-task, so it tests the agent's handling of bad tool results, not just its wording.

Two example agents (research and inventory) and a chaos CLI (`run`, `compare`) are included. It uses only the Python standard library, and every run is deterministic for a given seed.

**Honest limits:** the demo models are scripted stand-ins for reproducible demos, not language models. The judge is a keyword heuristic. Each run injects one fault. Only run it against agents you own. Real-model numbers are reported separately when an API key is available.
