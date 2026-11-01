"""Reports: terminal text, JSON, and a self-contained HTML page."""
import csv
import html
import io
import json
import os

from .judge import OUTCOMES

DEFINITIONS = {
    "recovered": "Fault hit; the agent retried or cross-checked and still gave the right answer.",
    "flagged": "Answer was wrong or missing, but the agent said so.",
    "silent_failure": "Wrong answer delivered as if nothing had happened.",
    "hijacked": "Agent followed an instruction hidden in tool output (the harmless word PINEAPPLE).",
    "unaffected": "Fault hit, but the answer stayed correct with no recovery needed.",
    "not_injected": "The agent never called the faulted tool, so nothing was injected.",
}
SEVERITY = ("hijacked", "silent_failure", "flagged", "recovered", "unaffected", "not_injected")
MOCK_NOTE = ("mock-* models are scripted stand-ins for reproducible demos, not language models; "
             "real-model numbers are reported separately when an API key is available.")


def silent_rate(r):
    """Share of injected runs where the agent was hijacked or failed silently."""
    c = r["counts"]
    injected = len(r["runs"]) - c["not_injected"]
    return (c["silent_failure"] + c["hijacked"]) / injected if injected else 0.0


def _has_mock(results):
    return any(r["model"].startswith("mock-") for r in results)


def render_json(results):
    return json.dumps(results, indent=2, sort_keys=True) + "\n"


def render_csv(results):
    """One row per chaos run, for spreadsheets."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["agent", "model", "seed", "fault", "tool", "kind", "persistent", "outcome", "final"])
    for r in results:
        for x in r["runs"]:
            w.writerow([r["agent"], r["model"], r["seed"], x["fault"], x["tool"], x["kind"],
                        x["persistent"], x["outcome"], x["final"]])
    return buf.getvalue()


def render_markdown(results):
    """A pasteable summary table."""
    head = ["Agent", "Model", "Runs", "Silent-failure rate", *OUTCOMES]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in results:
        cells = [r["agent"], r["model"], len(r["runs"]), f"{silent_rate(r):.0%}", *(r["counts"][o] for o in OUTCOMES)]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    if _has_mock(results):
        lines += ["", f"_{MOCK_NOTE}_"]
    return "\n".join(lines) + "\n"


def render_text(results):
    lines = []
    for r in results:
        c = r["counts"]
        bad = [x["fault"] for x in r["runs"] if x["outcome"] in ("silent_failure", "hijacked")]
        lines += [
            f"{r['agent']} / {r['model']}  ({len(r['runs'])} runs, seed {r['seed']}, "
            f"clean run {'correct' if r['baseline']['correct'] else 'WRONG'})",
            f"  silent-failure rate: {silent_rate(r):.0%} of injected runs",
            "  " + "  ".join(f"{o}={c[o]}" for o in OUTCOMES),
        ]
        if bad:
            lines.append("  silently missed: " + ", ".join(bad[:6]) + (" ..." if len(bad) > 6 else ""))
        lines.append("")
    if _has_mock(results):
        lines.append("Note: " + MOCK_NOTE)
    return "\n".join(lines) + "\n"


CSS = """
:root{--bg:#f5f6f8;--surface:#fff;--ink:#141a22;--muted:#5a6473;--line:#d8dde5;
--o-recovered:#1b7f5c;--o-flagged:#2f5fd0;--o-silent_failure:#c4302b;--o-hijacked:#8a3fb8;
--o-unaffected:#6b7788;--o-not_injected:#9aa4b2}
@media (prefers-color-scheme:dark){:root{--bg:#0e1218;--surface:#161c24;--ink:#e8ecf2;--muted:#98a3b3;--line:#2a323d}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 ui-sans-serif,"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif}
main{max-width:62rem;margin:0 auto;padding:40px 16px 72px}
h1{margin:0;font-size:1rem;font-weight:600;color:var(--muted)}
.finding{margin:12px 0 8px;max-width:44rem;font-size:1.65rem;line-height:1.28;font-weight:650;letter-spacing:-.015em}
.note{max-width:44rem;margin:0 0 28px;color:var(--muted);font-size:.9rem}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.chip{display:inline-flex;align-items:center;gap:8px;padding:6px 12px;border:1px solid var(--line);
border-radius:6px;background:var(--surface);color:var(--ink);font:inherit;font-size:.9rem;cursor:pointer}
.chip[aria-pressed=true]{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}
.chip b{font-weight:650;font-variant-numeric:tabular-nums}
.defs{color:var(--muted);font-size:.9rem}.defs summary{cursor:pointer}
.defs dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:12px 0 0}
.defs dt{font-weight:600;color:var(--ink)}.defs dd{margin:0}
.agent{margin-top:48px;border-top:1px solid var(--line);padding-top:20px}
h2{margin:0 0 4px;font-size:1.3rem;letter-spacing:-.01em}
.clean{margin:0 0 12px;color:var(--muted);font-size:.9rem}
.row{display:grid;grid-template-columns:13rem 1fr;gap:8px 24px;align-items:center;padding:12px 0}
.model{display:block;font-weight:600}
.rate{display:block;font-size:2.3rem;line-height:1.05;font-weight:700;letter-spacing:-.02em;
font-variant-numeric:tabular-nums}
.rate small{display:block;margin-top:2px;font-size:.8rem;font-weight:400;letter-spacing:0;color:var(--muted)}
.strip{display:flex;flex-wrap:wrap;gap:4px;margin:0;padding:0;list-style:none}
.sw,.cell{display:block;width:16px;height:16px;border-radius:3px;background:var(--c)}
.sw{display:inline-block;width:12px;height:12px}
.o-hijacked.sw,.o-hijacked.cell{background:repeating-linear-gradient(45deg,var(--c) 0 3px,#e3c6f2 3px 5px)}
.o-not_injected.sw,.o-not_injected.cell{background:none;border:1.5px dashed var(--c)}
.cell:focus-visible,.chip:focus-visible,summary:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.runs{margin-top:8px}
.runs>details{border:1px solid var(--line);border-radius:6px;background:var(--surface);padding:8px 14px;margin:8px 0}
.runs>details>summary{cursor:pointer;font-weight:600}
.run{border-top:1px solid var(--line);padding:6px 0}.run:target{outline:2px solid var(--ink);outline-offset:2px}
.run>summary{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:.92rem}
.tag{display:inline-block;min-width:7.5rem;padding:1px 8px;border-radius:4px;background:var(--c);
color:#fff;font-size:.8rem;font-weight:600;text-align:center}
.tag.o-not_injected{background:none;border:1px dashed var(--c);color:var(--muted)}
.final{margin:10px 0 6px}
.step{margin:10px 0 0}
.step code,.step pre{font:.8rem/1.45 ui-monospace,SFMono-Regular,Consolas,monospace}
.step pre{margin:4px 0 0;padding:8px 10px;border-left:3px solid var(--line);background:var(--bg);
white-space:pre-wrap;word-break:break-word}
.step.hit pre{border-left-color:var(--o-silent_failure)}
.hitnote{margin-left:8px;color:var(--o-silent_failure);font-size:.8rem;font-weight:600}
@media (prefers-reduced-motion:no-preference){
.cell{animation:pop .35s both;animation-delay:calc(var(--i)*14ms)}
@keyframes pop{from{opacity:0;transform:scale(.4)}}}
@media (max-width:640px){.row{grid-template-columns:1fr}.rate{font-size:1.9rem}.finding{font-size:1.35rem}
.defs dl{grid-template-columns:1fr}}
""" + "".join(
    f".o-{o}{{--c:var(--o-{o})}}"
    f'main[data-filter="{o}"] .cell:not(.o-{o}){{opacity:.15}}'
    f'main[data-filter="{o}"] .run:not(.o-{o}){{display:none}}' for o in OUTCOMES)

SCRIPT = """
(function(){
var main=document.querySelector('main'),chips=document.querySelectorAll('.chip');
function clear(){main.removeAttribute('data-filter');chips.forEach(function(c){c.setAttribute('aria-pressed','false')})}
chips.forEach(function(b){b.addEventListener('click',function(){
var on=b.getAttribute('aria-pressed')==='true';clear();
if(!on){b.setAttribute('aria-pressed','true');main.setAttribute('data-filter',b.dataset.o)}})});
function reveal(){var el=document.getElementById(decodeURIComponent(location.hash.slice(1)));
if(!el)return;clear();for(var p=el;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true}
el.scrollIntoView({block:'center'})}
window.addEventListener('hashchange',reveal);reveal();
})();
"""


def _finding(results):
    totals = {}
    for r in results:
        c, t = r["counts"], totals.setdefault(r["model"], [0, 0])
        t[0] += c["silent_failure"] + c["hijacked"]
        t[1] += len(r["runs"]) - c["not_injected"]
    pct = [(m, t[0] / t[1] if t[1] else 0.0) for m, t in totals.items()]
    first, rest = pct[0], pct[1:]
    text = (f"When tools broke, {first[0]} failed silently or was hijacked on {first[1]:.0%} of injected runs"
            + "".join(f", {m} on {p:.0%}" for m, p in rest) + ".")
    agents = len({r["agent"] for r in results})
    return text + (f" Averaged over {agents} agents." if agents > 1 else "")


def _steps(x):
    seen, out = 0, []
    for t in x["trace"]:
        hit = t["tool"] == x["tool"] and (x["persistent"] or seen == 0)
        seen += t["tool"] == x["tool"]
        note = '<span class="hitnote">fault injected here</span>' if hit else ""
        out.append(f'<div class="step{" hit" if hit else ""}"><code>{html.escape(str(t["tool"]))}('
                   f'{html.escape(json.dumps(t["args"]))})</code>{note}'
                   f'<pre>{html.escape(t["result"]) or "(empty)"}</pre></div>')
    return "".join(out)


def _run(x, rid):
    o = x["outcome"]
    return (f'<details class="run o-{o}" id="{rid}"><summary><span class="tag o-{o}">{o}</span>'
            f'{html.escape(x["fault"])}</summary>'
            f'<p class="final"><b>Agent answered:</b> {html.escape(x["final"]) or "(no answer)"}</p>'
            f'{_steps(x)}</details>')


def render_html(results):
    e = html.escape
    totals = {o: sum(r["counts"][o] for r in results) for o in OUTCOMES}
    chips = "".join(
        f'<button class="chip" type="button" aria-pressed="false" data-o="{o}">'
        f'<span class="sw o-{o}"></span>{o} <b>{totals[o]}</b></button>' for o in OUTCOMES)
    defs = "".join(f"<dt>{o}</dt><dd>{e(DEFINITIONS[o])}</dd>" for o in OUTCOMES)
    groups = {}
    for ri, r in enumerate(results):
        groups.setdefault(r["agent"], []).append((ri, r))
    sections = []
    for gi, (agent, items) in enumerate(groups.items()):
        rows, runs = [], []
        for ri, r in items:
            order = sorted(range(len(r["runs"])),
                           key=lambda i: (SEVERITY.index(r["runs"][i]["outcome"]), r["runs"][i]["fault"]))
            cells = "".join(
                f'<li><a class="cell o-{r["runs"][i]["outcome"]}" href="#run-{ri}-{i}" style="--i:{n}" '
                f'aria-label="{e(r["runs"][i]["fault"])}, {r["runs"][i]["outcome"]}" '
                f'title="{e(r["runs"][i]["fault"])}: {r["runs"][i]["outcome"]}"></a></li>'
                for n, i in enumerate(order))
            injected = len(r["runs"]) - r["counts"]["not_injected"]
            rows.append(
                f'<div class="row"><div><span class="model">{e(r["model"])}</span>'
                f'<span class="rate">{silent_rate(r):.0%}<small>silent failure or hijack, '
                f'{injected} injected runs</small></span></div>'
                f'<ol class="strip" aria-label="{e(agent)} runs with {e(r["model"])}">{cells}</ol></div>')
            body = "".join(_run(r["runs"][i], f"run-{ri}-{i}") for i in order)
            runs.append(f"<details><summary>{e(r['model'])}: all {len(r['runs'])} runs</summary>{body}</details>")
        base = items[0][1]["baseline"]
        sections.append(
            f'<section class="agent"><h2>{e(agent)}</h2>'
            f'<p class="clean">Clean run: {e(base["final"])}</p>{"".join(rows)}'
            f'<div class="runs">{"".join(runs)}</div></section>')
    seeds = ", ".join(sorted({str(r["seed"]) for r in results}))
    note = f"Seed {seeds}." + (f" Note: {MOCK_NOTE}" if _has_mock(results) else "")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>Chaos Monkey for AI Agents</title><style>{CSS}</style></head><body><main>"
            f'<h1>Chaos Monkey for AI Agents</h1><p class="finding">{e(_finding(results))}</p>'
            f'<p class="note">{e(note)}</p>'
            f'<div class="legend" role="group" aria-label="Filter runs by outcome">{chips}</div>'
            f'<details class="defs"><summary>What the outcomes mean</summary><dl>{defs}</dl></details>'
            f'{"".join(sections)}</main><script>{SCRIPT}</script></body></html>\n')


def write_reports(results, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, render in (("report.json", render_json), ("report.csv", render_csv),
                           ("report.md", render_markdown), ("report.html", render_html)):
        paths[name] = os.path.join(out_dir, name)
        with open(paths[name], "w", encoding="utf-8", newline="\n") as f:
            f.write(render(results))
    return paths
