"""Render a captured alignment report as a standalone, offline HTML file."""

from __future__ import annotations

import base64
import difflib
import hashlib
import html
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pstack_sync import AlignmentReport


def source_view(before: Optional[str], after: Optional[str], sources: dict) -> dict:
    left = before.splitlines(keepends=True) if before is not None else []
    right = after.splitlines(keepends=True) if after is not None else []
    for text in (before, after):
        if text is not None and text not in sources:
            sources[text] = len(sources)
    return {
        "left": sources.get(before),
        "right": sources.get(after),
        "blocks": difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes(),
    }


def script_hash(content: str) -> str:
    return base64.b64encode(hashlib.sha256(content.encode("utf-8")).digest()).decode("ascii")


def render(report: AlignmentReport) -> str:
    files = []
    sources = {}
    for entry in report.files:
        files.append({
            "path": entry.dstack_path,
            "upstream_path": entry.upstream_path,
            "status": entry.status,
            "upstream_sha256": entry.upstream_sha256,
            "dstack_sha256": entry.dstack_sha256,
            "binary": ((entry.upstream_sha256 is not None and entry.upstream_text is None)
                       or (entry.dstack_sha256 is not None and entry.dstack_text is None)),
            "raw": source_view(entry.upstream_text, entry.dstack_text, sources),
            "normalized": source_view(entry.normalized_upstream_text, entry.normalized_dstack_text, sources),
        })
    data = json.dumps({
        "files": files,
        "sources": [text.splitlines(keepends=True) for text in sources],
        "excluded": report.excluded,
        "owned": report.dstack_owned,
        "not_imported": report.not_imported,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    directory = Path(__file__).parent
    style = (directory / "pstack_alignment.css").read_text(encoding="utf-8")
    script = (directory / "pstack_alignment.js").read_text(encoding="utf-8")
    policy = "default-src 'none'; script-src 'sha256-{}'; style-src 'sha256-{}'; base-uri 'none'; form-action 'none'".format(
        script_hash(script), script_hash(style))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content=""" + '"' + html.escape(policy, quote=True) + '"' + """>
<title>pstack / dstack alignment</title>
<style>""" + style + """</style>
</head>
<body>
<header class="report-header">
<div class="report-toolbar"><div>
<h1>pstack <span aria-hidden="true">/</span> dstack</h1>
<p class="subtitle">A source snapshot, not a merge verdict.</p>
</div><label class="theme-control" for="theme">Appearance<select id="theme"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label></div>
<dl class="provenance"><div><dt>Upstream</dt><dd>""" + html.escape(report.repository) + """</dd></div>
<div><dt>Version</dt><dd>""" + html.escape(report.target_version) + """</dd></div>
<div><dt>Compared commit</dt><dd><code>""" + html.escape(report.target) + """</code></dd></div>
<div><dt>Pinned commit</dt><dd><code>""" + html.escape(report.pinned) + """</code></dd></div></dl>
<p class="muted">Local source text and content hashes are captured in this file. No network is needed. File permissions and live-harness behavior are not checked.</p>
</header>
<div id="alignment-summary" class="alignment-summary" aria-label="Alignment totals"></div>
<nav class="tabs" aria-label="Report sections">
<button type="button" id="compare-tab" aria-pressed="true">Compare files</button>
<button type="button" id="scope-tab" aria-pressed="false">Scope &amp; exclusions</button>
</nav>
<noscript>This report needs JavaScript enabled to navigate its embedded source snapshots. It does not load any external scripts.</noscript>
<section id="comparison" aria-label="Source comparison">
<div class="filters"><label>Find a skill or file<input id="search" type="search" placeholder="For example: interrogate" autocomplete="off"></label>
<label>Show<select id="status"><option value="all">All files</option><option value="different">Remaining differences</option>
<option value="rewritten">Mechanical rewrites only</option><option value="identical">Identical</option>
<option value="missing-local">Missing locally</option><option value="local-only">Local only</option></select></label>
<p id="file-count" role="status" aria-live="polite"></p></div>
<div class="workspace"><aside id="file-list" aria-label="Skills and playbooks"></aside>
<main id="file-view"><div class="file-heading"><h2 id="file-name">Select a file</h2><span id="file-status" class="badge"></span></div>
<div class="view-controls" role="group" aria-label="Comparison text"><button type="button" id="raw" aria-pressed="true">Original text</button>
<button type="button" id="normalized" aria-pressed="false">Normalized text</button>
<label><input id="changes-only" type="checkbox" checked> Collapse unchanged lines</label></div>
<p id="view-note" class="muted"></p><div id="diff"></div>
<details class="hashes"><summary>Snapshot paths &amp; SHA-256 hashes</summary><dl id="hash-values"></dl></details>
</main></div></section>
<section id="scope" aria-label="Supported scope and exclusions" hidden>
<h2>Scope &amp; exclusions</h2>
<p>Policy exclusions are not missing ports. Items without a recorded decision need an owner decision before import.</p>
<h3>Unsupported skills</h3><ul id="excluded-skills"></ul>
<h3>Unsupported playbooks</h3><ul id="excluded-playbooks"></ul>
<h3>Excluded files</h3><ul id="excluded-files"></ul>
<h3>Not imported, no exclusion decision recorded</h3><ul id="not-imported"></ul>
<h3>Dstack-owned skills &amp; sidecars</h3><p class="muted">Inventoried, not compared to upstream.</p><ul id="owned"></ul>
</section>
<script id="report-data" type="application/json">""" + data + """</script>
<script>""" + script + """</script>
</body>
</html>
"""
