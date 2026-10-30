#!/usr/bin/env python3
"""Absorb upstream pstack changes or inspect dstack's retained-tree alignment.

Reads the upstream repository, the pin, and the exclusion lists from
PSTACK_SYNC.md, shallow-fetches the pinned and target commits from that
repository (or reads a local --pstack-dir offline), diffs them, and three-way merges each kept file
after the mechanical rewrites. Anything matching a stop-and-ask rule is
reported instead of written. Exit status 1 means a decision is pending.
The separate --check-alignment mode reports whole-tree differences without
changing skills or the pin; its exit status 0 does not approve the differences.
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Pattern, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
SYNC_FILE = "PSTACK_SYNC.md"
PIN = re.compile(r"^Pinned: pstack (?P<version>\S+), commit `(?P<commit>[0-9a-f]{7,40})`\.$", re.M)
UPSTREAM = re.compile(r"^Upstream: repository `(?P<repo>[\w.-]+/[\w.-]+)`, subpath `(?P<subpath>[^`]*)`", re.M)
DEFAULT_TARGET = "main"
FULL_COMMIT = re.compile(r"[0-9a-f]{40}")
BULLET = re.compile(r"^- `([^`]+)`", re.M)
MODE = "poteto-mode"
SKILL_RENAMES = {"poteto-mode": "dstack-mode", "setup-pstack": "setup-dstack", "poteto-help": "dstack-help"}
NAME_REWRITES = tuple(SKILL_RENAMES.items()) + (
    ("poteto", "dstack"), ("Poteto", "Dstack"), ("pstack", "dstack"), ("Pstack", "Dstack"),
)
CURSOR_ONLY_FRONTMATTER = {"disable-model-invocation", "paths", "icon", "color"}
PORTABLE_FRONTMATTER = {"name", "description"}
CONFIG_CALL = "Call the Skill tool with `dstack-config`."
SENTENCE_DIRECTIVE = re.compile(r"(^|(?<=[.!?] ))(?:Run|Use|Invoke|Apply) the \*\*([a-z0-9-]+)\*\* skill\.", re.M)
ARROW_DIRECTIVE = re.compile(r"→ the \*\*([a-z0-9-]+)\*\* skill\.")
HOST_EXTRA = re.compile(
    r"`(?:Task|AskQuestion|TodoWrite|SwitchMode)`|\b(?:Task|AskQuestion|TodoWrite|SwitchMode) (?:tool|call)s?\b"
    r"|\.cursor/|\.mdc\b|\bmcps/|\bcursor-team-kit\b"
)
SPAWN_CONFIG = re.compile(
    r"\b(?:spawn\w*|sub-?agents?|effort|reasoning level|readonly|run_in_background|config\w*|profiles?)\b"
    r"|(?<!mental )(?<!data )(?<!domain )\bmodels?\b(?![- ]the[- ]domain)",
    re.I,
)


def load_audit():
    spec = importlib.util.spec_from_file_location("audit_portability", Path(__file__).with_name("audit_portability.py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit()
HOST_PATTERNS: Tuple[Pattern[str], ...] = tuple(
    pattern for label, pattern in AUDIT.LEAKAGE_PATTERNS if label != "legacy brand"
) + (HOST_EXTRA,)


@dataclass
class SyncConfig:
    repository: str
    subpath: str
    version: str
    commit: str
    excluded_skills: Set[str]
    excluded_playbooks: Set[str]
    excluded_files: List[str]
    owned: Set[str]


@dataclass
class AlignmentFile:
    upstream_path: Optional[str]
    dstack_path: str
    status: str
    upstream_sha256: Optional[str]
    dstack_sha256: Optional[str]
    diff: str = ""
    normalized_diff: str = ""
    upstream_text: Optional[str] = None
    dstack_text: Optional[str] = None
    normalized_upstream_text: Optional[str] = None
    normalized_dstack_text: Optional[str] = None


@dataclass
class AlignmentReport:
    repository: str
    pinned: str
    target: str
    target_version: str
    files: List[AlignmentFile]
    excluded: List[Tuple[str, str]]
    dstack_owned: List[str]
    not_imported: List[str]

    def render_html(self) -> str:
        spec = importlib.util.spec_from_file_location(
            "pstack_alignment_html", Path(__file__).with_name("pstack_alignment_html.py"))
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.render(self)

    def render(self) -> str:
        lines = [
            "# pstack alignment report", "",
            "- Repository: {}".format(self.repository),
            "- Pinned: `{}`".format(self.pinned),
            "- Compared: {} (`{}`)".format(self.target_version, self.target),
            "", "Informational, not an approval or live-harness check. Normalized matches use only the existing mechanical rewrites.",
        ]
        for status in ("identical", "rewritten", "different", "missing-local", "local-only"):
            entries = [entry for entry in self.files if entry.status == status]
            lines += ["", "## {} ({})".format(status, len(entries)), ""]
            if not entries:
                lines.append("None.")
            for entry in entries:
                lines.append("- `{}`{}".format(
                    entry.dstack_path,
                    " <- `{}`".format(entry.upstream_path) if entry.upstream_path else ""))
                diff = (entry.normalized_diff or entry.diff) if status not in {"identical", "rewritten"} else ""
                if diff:
                    fence = "`" * max(3, longest_backtick_run(diff) + 1)
                    lines += ["", fence + "diff", diff, fence]
        for heading, entries in (("Dstack-owned", self.dstack_owned), ("Not imported (no exclusion decision recorded)", self.not_imported)):
            lines += ["", "## " + heading, ""]
            lines += ["- `{}`".format(path) for path in entries] or ["None."]
        lines += ["", "## Excluded by policy", ""]
        lines += ["- `{}`: {}".format(path, reason) for path, reason in self.excluded] or ["None."]
        return "\n".join(lines) + "\n"


@dataclass
class Report:
    pinned: str
    target: str
    pinned_version: str
    target_version: str
    dry_run: bool
    decided: bool = False
    applied: List[Tuple[str, str]] = field(default_factory=list)
    skipped: List[Tuple[str, str]] = field(default_factory=list)
    decisions: List[Tuple[str, str]] = field(default_factory=list)
    details: Dict[str, List[Tuple[str, str, str]]] = field(default_factory=dict)
    pin_note: str = ""

    def decide(self, path: str, reason: str, *blocks: Tuple[str, str, str]) -> None:
        self.decisions.append((path, reason))
        kept = [block for block in blocks if block[2]]
        if kept:
            self.details[path] = kept

    def render(self) -> str:
        changed = self.applied or self.skipped or self.decisions
        decision_title = "Decided by hand" if self.decided else "Needs decision"
        result = "no-op" if not changed else "{} applied, {} skipped, {} {}".format(
            len(self.applied), len(self.skipped), len(self.decisions),
            "decided by hand" if self.decided else "need a decision")
        lines = [
            "# pstack sync report",
            "",
            "- Pinned: {} (`{}`)".format(self.pinned_version, self.pinned),
            "- Target: {} (`{}`)".format(self.target_version, self.target),
            "- Mode: {}".format("dry run" if self.dry_run else "write"),
            "- Result: {}".format(result),
        ]
        for title, items in (("Applied", self.applied), ("Skipped", self.skipped), (decision_title, self.decisions)):
            lines += ["", "## " + title, ""]
            if not items:
                lines.append("None.")
            for path, reason in items:
                if lines[-1].startswith("  `"):
                    lines.append("")
                lines.append("- `{}`: {}".format(path, reason))
                for label, language, body in self.details.get(path, []):
                    fence = "`" * max(3, longest_backtick_run(body) + 1)
                    lines += ["", "  " + label + ":", "", "  " + fence + language]
                    lines += [("  " + line).rstrip() for line in body.splitlines()]
                    lines.append("  " + fence)
        lines += ["", "## Pin", "", self.pin_note]
        return "\n".join(lines) + "\n"


def longest_backtick_run(text: str) -> int:
    return max((len(run) for run in re.findall(r"`+", text)), default=0)


def upstream_hunks(base: str, theirs: str) -> Tuple[str, str, str]:
    diff = difflib.unified_diff(base.splitlines(), theirs.splitlines(), n=1, lineterm="")
    return ("pstack change", "diff", "\n".join(list(diff)[2:]))


def clashing_lines(merged: str) -> Tuple[str, str, str]:
    blocks: List[str] = []
    current: Optional[List[str]] = None
    for line in merged.splitlines():
        if line.startswith("<<<<<<< "):
            current = []
        elif current is not None and (line.startswith("=======") or line.startswith("||||||| ")):
            blocks.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    return ("dstack lines it clashes with", "text", "\n...\n".join(blocks))


def section_bullets(text: str, heading: str) -> List[str]:
    match = re.search(r"^## {}\n(.*?)(?=^## |\Z)".format(re.escape(heading)), text, re.M | re.S)
    return BULLET.findall(match.group(1)) if match else []


def parse_sync(text: str) -> SyncConfig:
    pin = PIN.search(text)
    if not pin:
        raise SystemExit("{} has no 'Pinned: pstack <version>, commit `<sha>`.' line".format(SYNC_FILE))
    upstream = UPSTREAM.search(text)
    if not upstream:
        raise SystemExit("{} has no 'Upstream: repository `<owner/repo>`, subpath `<dir>/`' line".format(SYNC_FILE))
    return SyncConfig(
        repository=upstream.group("repo"),
        subpath=upstream.group("subpath"),
        version=pin.group("version"),
        commit=pin.group("commit"),
        excluded_skills=set(section_bullets(text, "Excluded skills")),
        excluded_playbooks=set(section_bullets(text, "Excluded playbooks")),
        excluded_files=section_bullets(text, "Excluded files"),
        owned=set(section_bullets(text, "Owned by dstack")),
    )


def rewrite_names(text: str) -> str:
    for old, new in NAME_REWRITES:
        text = text.replace(old, new)
    return text


def rewrite_directives(text: str, callable_skills: Set[str]) -> str:
    def call(name: str) -> str:
        return "Call the Skill tool with `{}`.".format(name)

    text = SENTENCE_DIRECTIVE.sub(
        lambda m: m.group(1) + call(m.group(2)) if m.group(2) in callable_skills else m.group(0), text)
    return ARROW_DIRECTIVE.sub(
        lambda m: "→ " + call(m.group(1)) if m.group(1) in callable_skills else m.group(0), text)


def split_frontmatter(text: str) -> Tuple[List[str], str]:
    if not text.startswith("---\n"):
        return [], text
    end = text.find("\n---\n", 4)
    if end < 0:
        return [], text
    return text[4:end].split("\n"), text[end:]


def frontmatter_keys(text: str) -> Set[str]:
    lines, _ = split_frontmatter(text)
    return {line.split(":", 1)[0].strip() for line in lines if line and not line[0].isspace() and ":" in line}


def take_cursor_frontmatter(text: str) -> Tuple[str, List[str]]:
    lines, rest = split_frontmatter(text)
    if not lines:
        return text, []
    kept: List[str] = []
    taken: List[str] = []
    dropping = False
    for line in lines:
        if line and not line[0].isspace() and not line.startswith("- "):
            dropping = line.split(":", 1)[0].strip() in CURSOR_ONLY_FRONTMATTER
        (taken if dropping else kept).append(line)
    return "---\n" + "\n".join(kept) + rest, taken


def strip_cursor_frontmatter(text: str) -> str:
    return take_cursor_frontmatter(text)[0]


def restore_frontmatter(text: str, lines: List[str]) -> str:
    current, rest = split_frontmatter(text)
    if not lines or not current:
        return text
    return "---\n" + "\n".join(current + lines) + rest


def rewrite(text: str, callable_skills: Set[str]) -> str:
    return strip_cursor_frontmatter(rewrite_directives(rewrite_names(text), callable_skills))


def mention_pattern(skills: Iterable[str], playbooks: Iterable[str]) -> Optional[Pattern[str]]:
    alternatives: List[str] = []
    for name in sorted(skills):
        escaped = re.escape(name)
        alternatives += [
            r"\*\*{}\*\*".format(escaped), r"`{}`".format(escaped), r"\.\./{}/".format(escaped),
            r"(?<![\w./-])/{}\b(?!-)".format(escaped), r"\b{} skill\b".format(escaped),
        ]
    for stem in sorted(playbooks):
        alternatives += [
            r"playbooks/{}\.md".format(re.escape(stem)),
            r"\*\*{}\.?\*\*".format(re.escape(stem.replace("-", " "))),
        ]
    return re.compile("|".join(alternatives), re.I) if alternatives else None


def line_changes(old: str, new: str) -> Tuple[List[str], List[str]]:
    a, b = old.splitlines(), new.splitlines()
    removed: List[str] = []
    added: List[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            removed += a[i1:i2]
            added += b[j1:j2]
    return removed, added


def merge(ours: str, base: str, theirs: str) -> Tuple[str, bool]:
    with tempfile.TemporaryDirectory() as temp:
        paths = []
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            path = Path(temp) / name
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        result = subprocess.run(["git", "merge-file", "-p", "--quiet", *paths], capture_output=True, text=True)
    if result.returncode < 0:
        raise SystemExit("git merge-file failed: " + result.stderr.strip())
    return result.stdout, result.returncode > 0


def run_git(*args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    command = ["git", "-c", "core.fsmonitor=false"] + (["-C", str(cwd)] if cwd else []) + list(args)
    return subprocess.run(command, capture_output=True)


def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "dstack" / "pstack-sync"


class Upstream:
    """Read-only view of pstack at two commits, in a fetched cache or a local folder."""

    def __init__(self, git_dir: Path, prefix: str, remote: Optional[str] = None):
        self.dir = git_dir
        self.prefix = prefix
        self.remote = remote

    @classmethod
    def fetched(cls, url: str, subpath: str, cache_dir: Path) -> "Upstream":
        repo = cache_dir / re.sub(r"[^A-Za-z0-9._-]+", "-", url).strip("-")
        if not (repo / "HEAD").is_file():
            repo.mkdir(parents=True, exist_ok=True)
            result = run_git("init", "--bare", "-q", str(repo))
            if result.returncode != 0:
                raise SystemExit("git init failed: " + result.stderr.decode().strip())
        return cls(repo, subpath, url)

    @classmethod
    def local(cls, folder: Path) -> "Upstream":
        folder = folder.resolve()
        for candidate in (folder, folder / "pstack"):
            if (candidate / "plugin.json").is_file() and (candidate / "skills").is_dir():
                prefix = run_git("rev-parse", "--show-prefix", cwd=candidate)
                if prefix.returncode != 0:
                    raise SystemExit("{} is not inside a git repository".format(candidate))
                return cls(candidate, prefix.stdout.decode().strip())
        raise SystemExit("{} is not a pstack folder (no plugin.json and skills/)".format(folder))

    def git(self, *args: str) -> str:
        result = run_git(*args, cwd=self.dir)
        if result.returncode != 0:
            raise SystemExit("git {} failed: {}".format(" ".join(args), result.stderr.decode().strip()))
        return result.stdout.decode()

    def commit(self, ref: str) -> str:
        if self.remote is None:
            return self.git("rev-parse", "--verify", ref + "^{commit}").strip()
        if re.fullmatch(r"[0-9a-f]{40}", ref) and run_git("cat-file", "-e", ref + "^{commit}", cwd=self.dir).returncode == 0:
            return ref
        self.git("fetch", "--quiet", "--depth=1", "--no-tags", self.remote, ref)
        return self.git("rev-parse", "--verify", "FETCH_HEAD^{commit}").strip()

    def show(self, commit: str, path: str) -> Optional[str]:
        content = self.show_bytes(commit, path)
        return content.decode("utf-8") if content is not None else None

    def show_bytes(self, commit: str, path: str) -> Optional[bytes]:
        result = run_git("show", "{}:{}{}".format(commit, self.prefix, path), cwd=self.dir)
        if result.returncode != 0:
            return None
        return result.stdout

    def files(self, commit: str) -> List[str]:
        output = self.git("ls-tree", "--full-tree", "-r", "--name-only", "-z", commit, "--", self.prefix + "skills/")
        return sorted(path[len(self.prefix):] for path in output.split("\0") if path)

    def version(self, commit: str) -> str:
        text = self.show(commit, "plugin.json") or ""
        match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        return match.group(1) if match else "unknown"

    def changes(self, old: str, new: str) -> List[Tuple[str, str]]:
        output = self.git("diff", "--no-renames", "--name-status", old, new)
        changes: List[Tuple[str, str]] = []
        for line in output.splitlines():
            status, _, path = line.partition("\t")
            if path.startswith(self.prefix):
                changes.append((status, path[len(self.prefix):]))
        return changes


def sync(
    target_ref: str = DEFAULT_TARGET,
    dstack_root: Path = ROOT,
    pstack_dir: Optional[Path] = None,
    repo_url: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    dry_run: bool = False,
    decided: bool = False,
) -> Report:
    if not dry_run and not FULL_COMMIT.fullmatch(target_ref):
        raise SystemExit(
            "A write run needs an explicit full target commit, not {!r}. Run --dry-run first and pass "
            "the Target commit it prints.".format(target_ref))
    sync_path = dstack_root / SYNC_FILE
    sync_text = sync_path.read_text(encoding="utf-8")
    config = parse_sync(sync_text)
    if pstack_dir is not None:
        upstream = Upstream.local(pstack_dir)
    else:
        url = repo_url or "https://github.com/{}.git".format(config.repository)
        upstream = Upstream.fetched(url, config.subpath, cache_dir or default_cache_dir())
    pinned = upstream.commit(config.commit)
    target = upstream.commit(target_ref)
    report = Report(pinned, target, config.version, upstream.version(target), dry_run, decided)

    skills_root = dstack_root / "skills"
    kept_skills = {path.name for path in skills_root.iterdir() if path.is_dir()}
    kept_playbooks = {path.stem for path in (skills_root / "dstack-mode" / "playbooks").glob("*.md")}
    names_kept = mention_pattern(kept_skills, kept_playbooks)
    names_excluded = mention_pattern(config.excluded_skills, config.excluded_playbooks)
    reported_dirs: Set[str] = set()
    outside: List[str] = []

    for status, path in upstream.changes(pinned, target):
        if not path.startswith("skills/"):
            outside.append(path)
            continue
        inner = path[len("skills/"):]
        top, _, rest = inner.partition("/")
        playbook = Path(rest).stem if top == MODE and rest.startswith("playbooks/") and rest.endswith(".md") else None
        excluded = (
            top in config.excluded_skills
            or (playbook is not None and playbook in config.excluded_playbooks)
            or any(fnmatch.fnmatch(inner, pattern) for pattern in config.excluded_files)
        )
        if excluded:
            old_text, new_text = upstream.show(pinned, path) or "", upstream.show(target, path) or ""
            removed, added = line_changes(old_text, new_text)
            if names_kept and any(names_kept.search(line) for line in removed + added):
                report.decide(path, "excluded upstream file changed in lines that name a kept skill or playbook",
                              upstream_hunks(old_text, new_text))
            else:
                report.skipped.append((path, "excluded"))
            continue
        if top in config.owned:
            report.decide(path, "owned by dstack; every upstream change needs a decision",
                          upstream_hunks(upstream.show(pinned, path) or "", upstream.show(target, path) or ""))
            continue
        local_top = SKILL_RENAMES.get(top, top)
        local = skills_root / local_top / rest
        local_rel = local.relative_to(dstack_root).as_posix()
        if local_top not in kept_skills:
            if top not in reported_dirs:
                reported_dirs.add(top)
                report.decisions.append(("skills/" + top, "new pstack skill; not imported"))
            continue
        if status == "D":
            what = "kept skill" if rest == "SKILL.md" else "kept playbook" if playbook else "kept file"
            report.decisions.append((path, "{} renamed or deleted upstream".format(what)))
            continue
        if status == "A" and playbook is not None:
            report.decisions.append((path, "new pstack playbook; not imported"))
            continue
        report_path = "{} <- {}".format(local_rel, path) if local_rel != path else local_rel
        try:
            base_raw = upstream.show(pinned, path) if status != "A" else ""
            theirs_raw = upstream.show(target, path)
        except UnicodeDecodeError:
            report.decisions.append((report_path, "binary file changed"))
            continue
        if base_raw is None or theirs_raw is None:
            report.decisions.append((report_path, "could not read upstream file"))
            continue
        base = rewrite(base_raw, kept_skills)
        theirs = rewrite(theirs_raw, kept_skills)
        if base == theirs:
            report.skipped.append((report_path, "only mechanically rewritten text changed"))
            continue
        if local.is_file():
            ours = local.read_text(encoding="utf-8")
        elif status == "A":
            ours = ""
        else:
            report.decisions.append((report_path, "dstack has no copy of this upstream file"))
            continue
        ours_body, ours_frontmatter = take_cursor_frontmatter(ours)
        merged, conflict = merge(ours_body, base, theirs)
        merged = restore_frontmatter(merged, ours_frontmatter)
        if not conflict and merged == ours:
            report.skipped.append((report_path, "already in dstack"))
            continue

        removed, added = line_changes(base, theirs)
        reasons: List[str] = []
        if conflict:
            reasons.append("lands in or next to lines dstack changed")
        if any(pattern.search(line) for pattern in HOST_PATTERNS for line in removed + added):
            reasons.append("host-specific tool, path, or name")
        new_keys = (frontmatter_keys(theirs) - frontmatter_keys(base)) - PORTABLE_FRONTMATTER
        if new_keys:
            reasons.append("new frontmatter key(s): " + ", ".join(sorted(new_keys)))
        if any(SPAWN_CONFIG.search(line) for line in removed + added):
            reasons.append("spawn, model, effort, or config wording")
        if names_excluded and any(names_excluded.search(line) for line in added):
            reasons.append("names an excluded skill or playbook")
        if any(AUDIT.LEGACY_SKILL_DIRECTIVE.search(line) and "Call the Skill tool with" not in line for line in added):
            reasons.append("skill call not in the exact Skill-tool phrase")
        if not conflict and merged.count(CONFIG_CALL) < ours.count(CONFIG_CALL):
            reasons.append("drops the dstack-config call line")
        if reasons:
            report.decide(report_path, "; ".join(reasons), upstream_hunks(base, theirs),
                          clashing_lines(merged) if conflict else ("", "", ""))
            continue
        if not dry_run:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(merged, encoding="utf-8")
        report.applied.append((report_path, "added" if status == "A" else "merged"))

    if outside:
        report.skipped.append(("{} path(s) outside skills/".format(len(outside)), "plugin packaging and docs"))

    if pinned == target:
        report.pin_note = "Pin unchanged: target is the pinned commit."
    elif dry_run:
        report.pin_note = "Pin unchanged: dry run. Write run: python3 scripts/pstack_sync.py {}".format(target)
    elif report.decisions and not decided:
        report.pin_note = "Pin unchanged: {} decision(s) pending.".format(len(report.decisions))
    else:
        line = "Pinned: pstack {}, commit `{}`.".format(report.target_version, target)
        sync_path.write_text(PIN.sub(line, sync_text, count=1), encoding="utf-8")
        report.pin_note = "Pin moved to {} (`{}`).".format(report.target_version, target[:7])
    return report


def alignment_diff(before: str, after: str, upstream_path: str, dstack_path: str) -> str:
    lines = difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=upstream_path, tofile=dstack_path)
    return "".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n" for line in lines).rstrip("\n")


def compare_file(
    upstream_path: str,
    local_path: str,
    before: Optional[bytes],
    after: Optional[bytes],
    skills: Set[str],
) -> AlignmentFile:
    entry = AlignmentFile(
        upstream_path if before is not None else None, local_path, "identical",
        hashlib.sha256(before).hexdigest() if before is not None else None,
        hashlib.sha256(after).hexdigest() if after is not None else None)
    for content, raw_field, normalized_field in (
        (before, "upstream_text", "normalized_upstream_text"),
        (after, "dstack_text", "normalized_dstack_text"),
    ):
        if content is not None:
            try:
                text = content.decode("utf-8")
                if "\0" not in text:
                    setattr(entry, raw_field, text)
                    setattr(entry, normalized_field, rewrite(text, skills))
            except UnicodeDecodeError:
                pass
    if before is None:
        entry.status = "local-only"
    elif after is None:
        entry.status = "missing-local"
    elif before == after:
        return entry
    else:
        entry.status = "different"
    try:
        before_text = (before or b"").decode("utf-8")
        after_text = (after or b"").decode("utf-8")
        if "\0" in before_text or "\0" in after_text:
            raise UnicodeError("binary content")
    except UnicodeError:
        entry.diff = "Binary content; compare the SHA-256 hashes in the JSON report."
        return entry
    before_label = "pstack/" + upstream_path if before is not None else "/dev/null"
    after_label = "dstack/" + local_path if after is not None else "/dev/null"
    entry.diff = alignment_diff(before_text, after_text, before_label, after_label)
    normalized_before = rewrite(before_text, skills)
    normalized_after = rewrite(after_text, skills)
    if before is not None and after is not None and normalized_before == normalized_after:
        entry.status = "rewritten"
    else:
        entry.normalized_diff = alignment_diff(normalized_before, normalized_after, before_label, after_label)
    return entry


def check_alignment(
    target_ref: Optional[str] = None,
    dstack_root: Path = ROOT,
    pstack_dir: Optional[Path] = None,
    repo_url: Optional[str] = None,
    cache_dir: Optional[Path] = None,
) -> AlignmentReport:
    text = (dstack_root / SYNC_FILE).read_text(encoding="utf-8")
    config = parse_sync(text)
    upstream = (Upstream.local(pstack_dir) if pstack_dir is not None else Upstream.fetched(
        repo_url or "https://github.com/{}.git".format(config.repository),
        config.subpath, cache_dir or default_cache_dir()))
    pinned = upstream.commit(config.commit)
    target = upstream.commit(target_ref) if target_ref else pinned
    upstream_files = upstream.files(target)
    skills_root = dstack_root / "skills"
    local_skills = {path.name for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    owned_skills = {SKILL_RENAMES.get(name, name) for name in config.owned}
    owned = {"skills/" + name for name in local_skills & owned_skills}
    excluded = []
    for heading, prefix, suffix in (
        ("Excluded skills", "skills/", ""),
        ("Excluded playbooks", "skills/" + MODE + "/playbooks/", ".md"),
        ("Excluded files", "skills/", ""),
    ):
        section = re.search(r"^## {}\n(.*?)(?=^## |\Z)".format(heading), text, re.M | re.S)
        if section:
            for match in re.finditer(r"^- `([^`]+)`(?::\s*(.*))?$", section.group(1), re.M):
                excluded.append((prefix + match.group(1) + suffix, match.group(2) or "Excluded by policy."))
    expected: Dict[str, str] = {}
    not_imported: Set[str] = set()
    for path in upstream_files:
        if path.count("/") < 2:
            continue
        _, name, rest = path.split("/", 2)
        local_name = SKILL_RENAMES.get(name, name)
        if name in config.excluded_skills or name in config.owned:
            continue
        if any(fnmatch.fnmatch(path[len("skills/"):], pattern) for pattern in config.excluded_files):
            continue
        if local_name not in local_skills:
            not_imported.add("skills/" + name)
            continue
        local_path = "skills/{}/{}".format(local_name, rest)
        if name == MODE and rest.startswith("playbooks/") and rest.endswith(".md"):
            if Path(rest).stem in config.excluded_playbooks:
                continue
            if not (dstack_root / local_path).is_file():
                not_imported.add(path)
                continue
        if rest == "agents/openai.yaml":
            continue
        expected[local_path] = path
    local_files: Dict[str, Path] = {}
    for name in sorted(local_skills - owned_skills):
        for path in sorted((skills_root / name).rglob("*")):
            if not AUDIT.is_package_asset(path) or path.name == ".DS_Store":
                continue
            local_path = path.relative_to(dstack_root).as_posix()
            if local_path == "skills/{}/agents/openai.yaml".format(name):
                owned.add(local_path)
            else:
                local_files[local_path] = path
    entries = []
    for local_path in sorted(set(expected) | set(local_files)):
        upstream_path = expected.get(local_path)
        before = upstream.show_bytes(target, upstream_path) if upstream_path else None
        if upstream_path and before is None:
            raise SystemExit("Could not read upstream file: " + upstream_path)
        after = local_files[local_path].read_bytes() if local_path in local_files else None
        entries.append(compare_file(upstream_path or "/dev/null", local_path, before, after, local_skills))
    return AlignmentReport(config.repository, pinned, target, upstream.version(target), entries,
                           sorted(excluded), sorted(owned), sorted(not_imported))


def main(argv: Sequence[str] = sys.argv[1:]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", nargs="?",
                        help="full target commit; read-only modes also take a branch or tag (default: main for sync, pin for alignment)")
    parser.add_argument("--pstack-dir", type=Path, help="offline only: read a local pstack folder instead of fetching")
    parser.add_argument("--dry-run", action="store_true", help="write nothing and leave the pin")
    parser.add_argument("--decided", action="store_true", help="every pending decision was settled by hand; move the pin")
    parser.add_argument("--check-alignment", action="store_true", help="read-only comparison of the retained tree to pstack (default: pinned commit)")
    parser.add_argument("--format", choices=("markdown", "json", "html"), default="markdown", help="alignment report format (default: markdown)")
    parser.add_argument("--report", type=Path, help="also write the report to this file")
    parser.add_argument("--cache-dir", type=Path, help="fetch cache (default: ~/.cache/dstack/pstack-sync)")
    parser.add_argument("--repo-url", help=argparse.SUPPRESS)
    parser.add_argument("--dstack-root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(list(argv))
    if args.check_alignment:
        if args.dry_run or args.decided:
            parser.error("--check-alignment cannot be combined with --dry-run or --decided")
        protected = [args.dstack_root] + ([args.pstack_dir] if args.pstack_dir else [])
        if args.report and any(
            args.report.resolve() == root.resolve() or root.resolve() in args.report.resolve().parents
            for root in protected
        ):
            parser.error("alignment report output must be outside the source trees")
        alignment = check_alignment(args.target, args.dstack_root, args.pstack_dir, args.repo_url, args.cache_dir)
        if args.format == "json":
            text = json.dumps(asdict(alignment), sort_keys=True, indent=2) + "\n"
        elif args.format == "html":
            text = alignment.render_html()
        else:
            text = alignment.render()
        sys.stdout.write(text)
        if args.report:
            args.report.write_text(text, encoding="utf-8")
        return 0
    if args.format != "markdown":
        parser.error("--format {} requires --check-alignment".format(args.format))
    if args.target is None and not args.dry_run:
        parser.error("a write run needs an explicit full target commit; run --dry-run first and pass the Target it prints")
    report = sync(
        args.target or DEFAULT_TARGET, args.dstack_root, pstack_dir=args.pstack_dir, repo_url=args.repo_url,
        cache_dir=args.cache_dir, dry_run=args.dry_run, decided=args.decided,
    )
    text = report.render()
    sys.stdout.write(text)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    return 1 if report.decisions and not args.decided else 0


if __name__ == "__main__":
    raise SystemExit(main())
