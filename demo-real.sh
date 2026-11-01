#!/usr/bin/env sh
# Run the chaos tests live against a real model and open the report.
# Default: a local Ollama model (no API key). For a hosted model set CHAOS_MODEL=anthropic:<id>
# or openai:<id> with the matching API key in your environment. RUNS and AGENT override the defaults.
set -eu
cd "$(dirname "$0")"

MODEL=${CHAOS_MODEL:-ollama:llama3.2}
RUNS=${RUNS:-20}
AGENT=${AGENT:-research}

PY=
for p in python3 python; do
  if "$p" -c '' >/dev/null 2>&1; then PY=$p; break; fi
done
[ -n "$PY" ] || { echo "python 3.10+ not found" >&2; exit 1; }

case "$MODEL" in
  ollama:*)
    name=${MODEL#ollama:}
    curl -sf http://127.0.0.1:11434/api/tags >/dev/null || {
      echo "Ollama is not running at 127.0.0.1:11434. Start it, or set CHAOS_MODEL to a hosted model." >&2; exit 1; }
    echo "Loading $name (the first call can take a minute)..."
    curl -sf -m 600 http://127.0.0.1:11434/api/generate \
      -d "{\"model\":\"$name\",\"prompt\":\"hi\",\"stream\":false,\"keep_alive\":\"30m\"}" >/dev/null || {
      echo "Could not load $name. Try: ollama pull $name" >&2; exit 1; }
    ;;
esac

echo "Running $RUNS chaos runs of the $AGENT agent against $MODEL"
"$PY" -m chaos_monkey run "$AGENT" --model "$MODEL" --runs "$RUNS" --seed 1 --live --out out-real

report="$PWD/out-real/report.html"
echo "Report: $report"
(xdg-open "$report" || open "$report" || cmd.exe /c start "" "$report") >/dev/null 2>&1 || true
