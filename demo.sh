#!/usr/bin/env sh
# Create a venv, run the tests, build the demo report, and open it.
set -eu
cd "$(dirname "$0")"

# Pick the first interpreter that actually runs (Windows has a python3 stub that does not).
PY=
for p in python3 python; do
  if "$p" -c '' >/dev/null 2>&1; then PY=$p; break; fi
done
[ -n "$PY" ] || { echo "python 3.10+ not found" >&2; exit 1; }

"$PY" -m venv .venv
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; else . .venv/Scripts/activate; fi

MAKE=$(command -v make || command -v mingw32-make)
"$MAKE" test
"$MAKE" demo

report="$PWD/out/report.html"
echo "Report: $report"
(xdg-open "$report" || open "$report" || cmd.exe /c start "" "$report") >/dev/null 2>&1 || true
