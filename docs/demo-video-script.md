# Demo video script (2 minutes)

Screen: terminal and the HTML report. Keep the mock-model disclosure in the voiceover.

**0:00 — The problem**
Say: "AI agents depend on tools, and tools fail. The dangerous failure isn't a crash. It's the agent that keeps going and gives you a confident, wrong answer. Chaos Monkey for AI Agents breaks the tools on purpose and measures what the agent silently gets wrong."

**0:15 — Run the demo**
Run: `./demo.sh`
Say: "One command: it runs the tests, then runs the chaos demo. Each run injects exactly one fault into one tool: empty output, an error, a timeout, truncated output, corrupted numbers, or a hidden instruction. The hidden instruction is just the word PINEAPPLE. The agent is never told."
Say: "These two agents are scripted mock models for reproducible demos. They are not language models."

**0:45 — Open one trace**
Open `out/report.html`, expand a `silent_failure` run for mock-naive (for example `fetch:corrupted`).
Say: "Here the fetch tool returned numbers that were slightly wrong. The agent trusted them and answered as if nothing happened. No error, no warning. That's a silent failure."

**1:15 — Compare naive and careful**
Scroll to the summary table.
Say: "Same faults, same seed, two agents. The naive one fails silently on almost every injected run. The careful one retries, cross-checks a second source, and when it can't confirm something it says so: recovered or flagged, never silent."

**1:45 — Real-model numbers**
If a real-model report exists, open `docs/real-model-report.html` and say: "Against a real model, over 20 chaos runs, the silent-failure rate was [X] percent." Fill in the number from the report.
If no real-model report exists, say: "Real-model numbers aren't in yet. Add an API key and the same command runs against a real model."

**1:55 — Call to action**
Say: "Chaos engineering for AI agents. Point it at an agent you own, and find out what it silently gets wrong before your users do. Code is on GitHub."
