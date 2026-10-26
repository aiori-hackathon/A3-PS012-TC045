"""Builds the exposure assessment report from one run: report.html, summary.md, scores.json and (optionally) report.pdf."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment
from markupsafe import Markup

from resolverlens import __version__
from resolverlens.classify import AUTHORITATIVE_ONLY, INCONCLUSIVE, LABELS, RECURSIVE, REFUSED, classify_run
from resolverlens.compare import behaviors as seeded_behaviors, compare, expected_labels
from resolverlens.evidence import read_evidence
from resolverlens.score import (REMEDIATION, compliance, confusion, inconclusive_table, per_class, root_cause, summary)

LABEL_TEXT = {RECURSIVE: "Recursive", AUTHORITATIVE_ONLY: "Authoritative-only", REFUSED: "Refused", INCONCLUSIVE: "Inconclusive"}
COLOUR = {RECURSIVE: "#c0392b", AUTHORITATIVE_ONLY: "#1b8a4b", REFUSED: "#0000cc", INCONCLUSIVE: "#d97706"}


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _num(x):
    return "n/a" if x is None else f"{x:.2f}"


def bar_svg(counts: dict, total: int) -> Markup:
    if not total:
        return Markup("")
    x, parts = 0.0, []
    for lab in LABELS:
        w = 600.0 * counts.get(lab, 0) / total
        if w:
            parts.append(f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="26" fill="{COLOUR[lab]}"/>'
                         f'<text x="{x + w / 2:.1f}" y="17" fill="#fff" font-size="11" text-anchor="middle">{counts[lab]}</text>')
            x += w
    legend = "".join(f'<span style="color:{COLOUR[l]}">&#9632;</span> {LABEL_TEXT[l]} ({counts.get(l, 0)}) &nbsp; ' for l in LABELS)
    return Markup(f'<svg width="600" height="26" viewBox="0 0 600 26">{"".join(parts)}</svg><div class="legend">{legend}</div>')


CSS = """
@page { size: A4; margin: 14mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10pt; color: #111; line-height: 1.35; }
h1 { color: #0000cc; font-size: 20pt; margin: 0 0 4px; } h2 { color: #0000cc; font-size: 13pt; margin: 18px 0 6px; border-bottom: 1px solid #0000cc; }
h3 { font-size: 10.5pt; margin: 10px 0 4px; } table { border-collapse: collapse; width: 100%; margin: 6px 0; }
th, td { border: 1px solid #999; padding: 3px 5px; text-align: left; vertical-align: top; font-size: 8.5pt; } th { background: #0000cc; color: #fff; }
.num { text-align: center; } .ok { color: #1b8a4b; font-weight: bold; } .bad { color: #c0392b; font-weight: bold; }
.box { background: #eef1ff; border-left: 4px solid #0000cc; padding: 6px 10px; margin: 6px 0; } .small { font-size: 8pt; color: #444; }
.card { page-break-inside: avoid; margin: 8px 0; } .legend { font-size: 8.5pt; margin-top: 3px; } code { font-size: 8pt; }
tr { page-break-inside: avoid; } h2, h3 { page-break-after: avoid; }
.diag { background: #cdebd8; } .off { background: #f6d5d1; } .zero { color: #888; }
"""

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>DNS Resolver Exposure Assessment Report: {{ run.run_id }}</title>
<style>{{ css }}</style></head><body>
<h1>DNS Resolver Exposure Assessment Report</h1>
<div class="small">Team A3-PS012-TC045 &middot; AIORI Hackathon 3 &middot; PS-012 &middot; ResolverLens {{ version }} &middot; run <b>{{ run.run_id }}</b>
&middot; started {{ run.started_utc }} &middot; {{ sm.total }} authorised lab servers &middot; {{ run.probes }} probes in {{ run.duration_s }} s</div>

<h2>1. Summary</h2>
<div class="box">
<b>{{ exposed|length }} of {{ sm.total }}</b> servers provide recursion to the external client:
{% for r in exposed %}{{ r.target_id }} ({{ r.software }}){{ ", " if not loop.last }}{% else %}none{% endfor %}.
{% if sm.wrong_decisions == 0 and sm.false_exposure == 0 and sm.missed_exposure == 0 %}
Every decisive verdict matches the seeded ground truth. {% endif %}
Accuracy {{ pct(sm.accuracy) }} ({{ sm.correct }}/{{ sm.total }}), accuracy on decided cases {{ pct(sm.accuracy_decided) }}, coverage {{ pct(sm.coverage) }}
({{ sm.decided }} of {{ sm.total }} servers decided; {{ sm.abstained_correctly }} correctly reported as Inconclusive).
</div>
{{ bar }}
<p class="small">How to read the labels. <b>Recursive</b>: the server looked up a name for the external client (proved by our own canary server's log).
<b>Authoritative-only</b>: it answers its own zone but does not recurse. <b>Refused</b>: it denies the external client. <b>Inconclusive</b>: the evidence is missing or
contradictory, and the reason is recorded. Verdicts follow the rules on the method page (section 9).</p>

<h2>2. Findings per server</h2>
<table><tr><th>Server</th><th>Address</th><th>Software</th><th>Verdict</th><th>Reason</th><th>Canary evidence (who asked the canary)</th>
<th>Ground truth (lab only)</th><th>Match</th></tr>
{% for r in rows %}<tr><td>{{ r.target_id }}</td><td>{{ r.ip }}</td><td>{{ r.software }}</td>
<td style="color:{{ colour[r.label] }}"><b>{{ text[r.label] }}</b></td><td>{{ r.reason or "-" }}</td><td>{{ r.sources or "-" }}</td>
<td>{{ text[r.expected] }}</td><td class="{{ 'ok' if r.match else 'bad' }}">{{ "yes" if r.match else "NO" }}</td></tr>{% endfor %}</table>
<p class="small">The ground-truth column exists only because this is a seeded lab. A real assessment has no such column.</p>

<h2>3. Evaluation against the seeded ground truth</h2>
<p>Rows are the expected labels, columns are what ResolverLens reported. Green cells are correct, red cells are errors.</p>
<table><tr><th>Expected \\ Reported</th>{% for c in classes %}<th class="num">{{ text[c] }}</th>{% endfor %}<th class="num">Total</th></tr>
{% for e in classes %}<tr><td><b>{{ text[e] }}</b></td>
{% for c in classes %}<td class="num {{ 'diag' if e == c else ('off' if matrix[e][c] else 'zero') }}">{{ matrix[e][c] }}</td>{% endfor %}
<td class="num">{{ pc[e].support }}</td></tr>{% endfor %}</table>
<table><tr><th>Class</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">F1</th><th class="num">Expected</th><th class="num">Reported</th></tr>
{% for c in classes %}<tr><td>{{ text[c] }}</td><td class="num">{{ num(pc[c].precision) }}</td><td class="num">{{ num(pc[c].recall) }}</td>
<td class="num">{{ num(pc[c].f1) }}</td><td class="num">{{ pc[c].support }}</td><td class="num">{{ pc[c].reported }}</td></tr>{% endfor %}</table>
<table><tr><th>Measure</th><th>Value</th><th>Meaning</th></tr>
<tr><td>Accuracy</td><td>{{ pct(sm.accuracy) }}</td><td>Verdicts equal to the expected label, over all servers</td></tr>
<tr><td>Accuracy on decided cases</td><td>{{ pct(sm.accuracy_decided) }}</td><td>Correct verdicts among servers where the tool gave a decisive label</td></tr>
<tr><td>Coverage</td><td>{{ pct(sm.coverage) }}</td><td>Share of servers the tool decided instead of reporting Inconclusive</td></tr>
<tr><td>Wrong decisions</td><td>{{ sm.wrong_decisions }}</td><td>Decisive verdicts that disagree with the expected label (the costly error)</td></tr>
<tr><td>False exposure / missed exposure</td><td>{{ sm.false_exposure }} / {{ sm.missed_exposure }}</td><td>Reported Recursive when it should not be / failed to report Recursive when it should</td></tr>
<tr><td>Correct abstentions</td><td>{{ sm.abstained_correctly }}</td><td>Inconclusive reported for servers seeded as unusable</td></tr></table>

<h2>4. False and inconclusive result analysis</h2>
<h3>4.1 False results</h3>
{% if faults %}<table><tr><th>Server</th><th>Expected</th><th>Reported</th><th>Likely cause</th><th>Explanation</th></tr>
{% for f in faults %}<tr><td>{{ f.target_id }}</td><td>{{ text[f.expected] }}</td><td>{{ text[f.label] }}</td><td>{{ f.cause.category }}</td><td>{{ f.cause.explanation }}</td></tr>{% endfor %}</table>
{% else %}<div class="box">No false results in this run: all {{ sm.total }} verdicts equal their expected labels. Each false result would be listed here with a likely cause (ACL, caching, forwarder chain, packet loss, rate limiting, upstream failure).</div>{% endif %}
<h3>4.2 Inconclusive results</h3>
{% if inc %}<table><tr><th>Server</th><th>Software</th><th>Reason</th><th>Likely cause</th><th>Why the tool did not guess</th><th>Seeded as (lab only)</th><th>Expected?</th></tr>
{% for i in inc %}<tr><td>{{ i.target_id }}</td><td>{{ i.software }}</td><td>{{ i.reason }}</td><td>{{ i.likely_cause }}</td><td>{{ i.meaning }}{% if i.late_hits %} A canary lookup happened ({{ i.late_hits }}) but the reply never reached us, so it does not count as recursion.{% endif %}</td>
<td>{{ i.seeded }}</td><td class="{{ 'ok' if i.expected_inconclusive else 'bad' }}">{{ "yes" if i.expected_inconclusive else "NO" }}</td></tr>{% endfor %}</table>
{% else %}<div class="box">No inconclusive results in this run.</div>{% endif %}

<h2>5. Exposure and remediation</h2>
{% if exposed %}<p>RFC 5358 asks operators to offer recursion only to their intended clients. The following servers answered an external client:</p>
<table><tr><th>Server</th><th>Software</th><th>Suggested change (check the syntax for your version)</th></tr>
{% for r in exposed %}<tr><td>{{ r.target_id }} ({{ r.ip }})</td><td>{{ r.software }}</td><td><code>{{ remedy[r.software] }}</code>{% if r.sources and r.sources != r.ip %}<br>Its lookups came from {{ r.sources }}: that upstream server needs the same restriction.{% endif %}</td></tr>{% endfor %}</table>
{% else %}<p>No server provided recursion to the external client.</p>{% endif %}

<h2>6. Safety and compliance, measured from the evidence</h2>
<table><tr><th>Check</th><th>Observed</th><th>Limit or rule</th></tr>
<tr><td>Destinations contacted</td><td>{{ comp.destinations }} (all on the allowlist: {{ "yes" if comp.all_destinations_on_allowlist else "NO" }})</td><td>at most 20 authorised lab servers</td></tr>
<tr><td>Query types sent</td><td>{{ comp.query_types|join(", ") }}</td><td>type A only, never ANY</td></tr>
<tr><td>Peak rate, all targets together</td><td>{{ comp.max_queries_per_second_all_targets }} queries in any second</td><td>{{ comp.limits.global_rate }} per second plus burst</td></tr>
<tr><td>Peak rate, one target</td><td>{{ comp.max_queries_per_second_one_target }} queries in any second</td><td>{{ comp.limits.per_target_rate }} per second plus burst</td></tr>
<tr><td>Largest reply / reply-to-query ratio</td><td>{{ comp.max_reply_bytes }} bytes / {{ comp.max_reply_to_query_ratio }}</td><td>{{ comp.limits.max_reply_bytes }} bytes / {{ comp.limits.max_ratio }}</td></tr>
<tr><td>How the run ended</td><td>{{ comp.stop_reason }}</td><td>safety tripwire and stop file available</td></tr></table>
<p class="small">The tool has no spoofing option: every query leaves from the probe client's own address. The lab network has no Internet access.</p>

<h2>7. Evidence per server</h2>
{% for c in cards %}<div class="card"><h3>{{ c.target_id }} &middot; {{ c.ip }} &middot; {{ c.software }} &middot; <span style="color:{{ colour[c.label] }}">{{ text[c.label] }}</span>{% if c.reason %} ({{ c.reason }}){% endif %}</h3>
<div class="small">{{ c.detail }} (rule {{ c.rule }})</div>
<table><tr><th>Query</th><th>RD</th><th>Status</th><th>RA</th><th>AA</th><th>Answer</th><th>Canary log</th><th>ms</th></tr>
{% for r in c.records %}<tr><td>{{ r.phase }} {{ r.attempt or "" }}: {{ r.qname }}</td><td class="num">{{ "1" if r.rd else "0" }}</td><td>{{ r.status }}{% if r.tcp_retry %} (tcp){% endif %}</td>
<td class="num">{{ "1" if r.flags.get("ra") else "0" }}</td><td class="num">{{ "1" if r.flags.get("aa") else "0" }}</td><td>{{ r.answers|join(", ") or "-" }}</td>
<td>{% if r.canary_hit %}seen from {{ r.canary_sources|join(", ") }}{% else %}-{% endif %}</td><td class="num">{{ r.rtt_ms if r.rtt_ms is not none else "-" }}</td></tr>{% endfor %}</table></div>{% endfor %}

<h2>8. Reproducibility</h2>
<table><tr><th>Item</th><th>Value</th></tr>
<tr><td>Run, seed, tool version</td><td>{{ run.run_id }}, {{ run.seed }}, {{ version }}</td></tr>
<tr><td>Config digest (settings and targets file)</td><td><code>{{ run.config_digest }}</code></td></tr>
<tr><td>Timeout, attempts, EDNS buffer</td><td>{{ run.config.probe.timeout_s }} s, {{ run.config.probe.attempts }}, {{ run.config.probe.edns_payload }} bytes</td></tr>
<tr><td>Re-run</td><td><code>make probe RUN=&lt;name&gt;</code> then <code>make report RUN=&lt;name&gt;</code>. The same seed and run id give the same canary names, and the verdicts are computed from evidence.jsonl alone.</td></tr></table>

<h2>9. Method: the four rules</h2>
<p>Each server receives one baseline query (RD off, a name in its own zone) and {{ run.config.probe.attempts }} canary queries (RD on, a fresh unique name each time, in a zone served only by our canary server).
The canary server logs every query it receives. Rules are checked in order and the first match decides:</p>
<table><tr><th>Rule</th><th>Verdict</th><th>Condition</th></tr>
<tr><td>1</td><td>Recursive</td><td>Every canary attempt is NOERROR with RA set, the marker answer, and a hit in the canary log</td></tr>
<tr><td>2</td><td>Refused</td><td>The baseline and every canary attempt are REFUSED</td></tr>
<tr><td>3</td><td>Authoritative-only</td><td>The baseline is answered with AA; every canary attempt gets a reply with no answer, no RA and no canary hit</td></tr>
<tr><td>4</td><td>Inconclusive</td><td>Anything else, with a reason: TIMEOUT, SERVFAIL, TC_FAIL, CONFLICT, ERROR or NO_DATA</td></tr></table>
</body></html>"""


def _records_by_target(evidence):
    by: dict[str, list] = {}
    for r in evidence:
        by.setdefault(r["target_id"], []).append(r)
    return by


def build_report(run_dir, targets_file=None, pdf=False) -> dict:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    tf = targets_file or manifest["config"]["targets_file"]
    verdicts = classify_run(run_dir, tf)
    expected = expected_labels(tf)
    rows = compare(verdicts, expected)
    evidence = list(read_evidence(run_dir / "evidence.jsonl"))
    by_t = _records_by_target(evidence)
    vmap = {v.target_id: v for v in verdicts}
    for r in rows:
        v = vmap[r["target_id"]]
        r.update(ip=v.ip, sources=", ".join(v.canary_sources))
    matrix, sm = confusion(rows), summary(rows)
    pc, comp = per_class(matrix), compliance(evidence, manifest)
    faults = [dict(r, cause=root_cause(r, vmap[r["target_id"]])) for r in rows if not r["match"]]
    exposed = [r for r in rows if r["label"] == RECURSIVE]
    cards = [{"target_id": v.target_id, "ip": v.ip, "software": v.software, "label": v.label, "reason": v.reason,
              "rule": v.rule, "detail": v.detail, "records": by_t.get(v.target_id, [])} for v in verdicts]
    counts = {lab: sum(1 for r in rows if r["label"] == lab) for lab in LABELS}
    env = Environment(autoescape=True)
    html = env.from_string(HTML).render(
        css=Markup(CSS), version=__version__, run=_Obj(manifest), sm=_Obj(sm), rows=[_Obj(r) for r in rows], exposed=[_Obj(r) for r in exposed],
        matrix=matrix, pc={k: _Obj(v) for k, v in pc.items()}, classes=LABELS, faults=[_Obj(f) for f in faults],
        inc=[_Obj(i) for i in inconclusive_table(verdicts, expected, seeded_behaviors(tf))], remedy=REMEDIATION, comp=_Obj(comp),
        cards=[_Obj(c) for c in cards], text=LABEL_TEXT, colour=COLOUR, bar=bar_svg(counts, len(rows)), pct=_pct, num=_num)
    out = {"html": run_dir / "report.html", "summary": run_dir / "summary.md", "scores": run_dir / "scores.json"}
    out["html"].write_text(html)
    out["scores"].write_text(json.dumps({"summary": sm, "confusion": matrix, "per_class": pc, "compliance": comp,
                                         "false_results": [{k: f[k] for k in ("target_id", "expected", "label")} | {"cause": f["cause"]} for f in faults],
                                         "inconclusive": inconclusive_table(verdicts, expected, seeded_behaviors(tf))}, indent=2, sort_keys=True) + "\n")
    out["summary"].write_text(_markdown(manifest, rows, matrix, sm, exposed))
    if pdf:
        try:
            import weasyprint
            weasyprint.HTML(filename=str(out["html"])).write_pdf(str(run_dir / "report.pdf"))
            out["pdf"] = run_dir / "report.pdf"
        except Exception as e:   # missing package or system libraries: the HTML can still be printed to PDF
            out["pdf_error"] = f"{type(e).__name__}: {e}"
    out["summary_numbers"] = sm
    return out


class _Obj(dict):
    """A dict whose keys can be read as attributes inside the template."""
    def __getattr__(self, k):
        try:
            v = self[k]
        except KeyError:
            raise AttributeError(k) from None
        return _Obj(v) if isinstance(v, dict) and not isinstance(v, _Obj) else v


def _markdown(manifest, rows, matrix, sm, exposed) -> str:
    L = [f"# Assessment summary: run {manifest['run_id']}", "",
         f"- Servers assessed: **{sm['total']}**; providing recursion to the external client: **{len(exposed)}** ({', '.join(r['target_id'] for r in exposed) or 'none'})",
         f"- Accuracy {_pct(sm['accuracy'])} ({sm['correct']}/{sm['total']}); accuracy on decided cases {_pct(sm['accuracy_decided'])}; coverage {_pct(sm['coverage'])}",
         f"- Wrong decisions: {sm['wrong_decisions']}; correct abstentions: {sm['abstained_correctly']}", "",
         "## Confusion matrix (rows expected, columns reported)", "",
         "| Expected \\ Reported | " + " | ".join(LABEL_TEXT[c] for c in LABELS) + " |", "|---|" + "---|" * len(LABELS)]
    for e in LABELS:
        L.append(f"| {LABEL_TEXT[e]} | " + " | ".join(str(matrix[e][c]) for c in LABELS) + " |")
    L += ["", "## Verdicts", "", "| Server | Software | Verdict | Reason | Expected | Match |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['target_id']} | {r['software']} | {LABEL_TEXT[r['label']]} | {r['reason'] or '-'} | {LABEL_TEXT[r['expected']]} | {'yes' if r['match'] else 'NO'} |")
    return "\n".join(L) + "\n"
