#!/usr/bin/env python3
"""Absorb upstream pstack changes into dstack's kept skills.

Reads the pin and the exclusion lists from PSTACK_SYNC.md, diffs the pinned
pstack commit against a target commit, and three-way merges each kept file
after the mechanical rewrites. Anything matching a stop-and-ask rule is
reported instead of written. Exit status 1 means a decision is pending.
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import importlib.util
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Pattern, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
SYNC_FILE = "PSTACK_SYNC.md"
PIN = re.compile(r"^Pinned: pstack (?P<version>\S+), commit `(?P<commit>[0-9a-f]{7,40})`\.$", re.M)
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
    version: str
    commit: str
    excluded_skills: Set[str]
    excluded_playbooks: Set[str]
    excluded_files: List[str]
    owned: Set[str]


@dataclass
class Report:
    pinned: str
    target: str
    pinned_version: str
    target_version: str
    dry_run: bool
    applied: List[Tuple[str, str]] = field(default_factory=list)
    skipped: List[Tuple[str, str]] = field(default_factory=list)
    decisions: List[Tuple[str, str]] = field(default_factory=list)
    pin_note: str = ""

    def render(self) -> str:
        changed = self.applied or self.skipped or self.decisions
        result = "no-op" if not changed else "{} applied, {} skipped, {} need a decision".format(
            len(self.applied), len(self.skipped), len(self.decisions))
        lines = [
            "# pstack sync report",
            "",
            "- Pinned: {} (`{}`)".format(self.pinned_version, self.pinned[:7]),
            "- Target: {} (`{}`)".format(self.target_version, self.target[:7]),
            "- Mode: {}".format("dry run" if self.dry_run else "write"),
            "- Result: {}".format(result),
        ]
        for title, items in (("Applied", self.applied), ("Skipped", self.skipped), ("Needs decision", self.decisions)):
            lines += ["", "## " + title, ""]
            lines += ["- `{}`: {}".format(path, reason) for path, reason in items] or ["None."]
        lines += ["", "## Pin", "", self.pin_note]
        return "\n".join(lines) + "\n"


def section_bullets(text: str, heading: str) -> List[str]:
    match = re.search(r"^## {}\n(.*?)(?=^## |\Z)".format(re.escape(heading)), text, re.M | re.S)
    return BULLET.findall(match.group(1)) if match else []


def parse_sync(text: str) -> SyncConfig:
    pin = PIN.search(text)
    if not pin:
        raise SystemExit("{} has no 'Pinned: pstack <version>, commit `<sha>`.' line".format(SYNC_FILE))
    return SyncConfig(
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


def strip_cursor_frontmatter(text: str) -> str:
    lines, rest = split_frontmatter(text)
    if not lines:
        return text
    kept: List[str] = []
    dropping = False
    for line in lines:
        if line and not line[0].isspace() and not line.startswith("- "):
            dropping = line.split(":", 1)[0].strip() in CURSOR_ONLY_FRONTMATTER
        if not dropping:
            kept.append(line)
    return "---\n" + "\n".join(kept) + rest


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


class Upstream:
    def __init__(self, checkout: Path):
        checkout = checkout.resolve()
        for candidate in (checkout, checkout / "pstack"):
            if (candidate / "plugin.json").is_file() and (candidate / "skills").is_dir():
                self.dir = candidate
                break
        else:
            raise SystemExit("{} is not a pstack checkout (no plugin.json and skills/)".format(checkout))
        self.prefix = self.git("rev-parse", "--show-prefix").strip()

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(self.dir), *args], capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit("git {} failed: {}".format(" ".join(args), result.stderr.strip()))
        return result.stdout

    def commit(self, ref: str) -> str:
        return self.git("rev-parse", "--verify", ref + "^{commit}").strip()

    def show(self, commit: str, path: str) -> Optional[str]:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", str(self.dir), "show", "{}:{}{}".format(commit, self.prefix, path)], capture_output=True)
        if result.returncode != 0:
            return None
        return result.stdout.decode("utf-8")

    def version(self, commit: str) -> str:
        text = self.show(commit, "plugin.json") or ""
        match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        return match.group(1) if match else "unknown"

    def changes(self, old: str, new: str) -> List[Tuple[str, str]]:
        output = self.git("diff", "--relative", "--no-renames", "--name-status", old, new)
        return [tuple(line.split("\t", 1)) for line in output.splitlines() if line]  # type: ignore[misc]


def sync(
    checkout: Path,
    target_ref: str,
    dstack_root: Path = ROOT,
    dry_run: bool = False,
    decided: bool = False,
) -> Report:
    sync_path = dstack_root / SYNC_FILE
    sync_text = sync_path.read_text(encoding="utf-8")
    config = parse_sync(sync_text)
    upstream = Upstream(checkout)
    pinned = upstream.commit(config.commit)
    target = upstream.commit(target_ref)
    report = Report(pinned, target, config.version, upstream.version(target), dry_run)

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
            removed, added = line_changes(upstream.show(pinned, path) or "", upstream.show(target, path) or "")
            if names_kept and any(names_kept.search(line) for line in removed + added):
                report.decisions.append((path, "excluded upstream file changed in lines that name a kept skill or playbook"))
            else:
                report.skipped.append((path, "excluded"))
            continue
        if top in config.owned:
            report.decisions.append((path, "owned by dstack; every upstream change needs a decision"))
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
        merged, conflict = merge(ours, base, theirs)
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
            report.decisions.append((report_path, "; ".join(reasons)))
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
        report.pin_note = "Pin unchanged: dry run."
    elif report.decisions and not decided:
        report.pin_note = "Pin unchanged: {} decision(s) pending.".format(len(report.decisions))
    else:
        line = "Pinned: pstack {}, commit `{}`.".format(report.target_version, target)
        sync_path.write_text(PIN.sub(line, sync_text, count=1), encoding="utf-8")
        report.pin_note = "Pin moved to {} (`{}`).".format(report.target_version, target[:7])
    return report


def main(argv: Sequence[str] = sys.argv[1:]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pstack", type=Path, help="pstack checkout (the plugin folder or the plugins repository)")
    parser.add_argument("target", help="target pstack commit")
    parser.add_argument("--dry-run", action="store_true", help="write nothing and leave the pin")
    parser.add_argument("--decided", action="store_true", help="every pending decision was settled by hand; move the pin")
    parser.add_argument("--report", type=Path, help="also write the report to this file")
    parser.add_argument("--dstack-root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(list(argv))
    report = sync(args.pstack, args.target, args.dstack_root, args.dry_run, args.decided)
    text = report.render()
    sys.stdout.write(text)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    return 1 if report.decisions and not args.decided else 0


if __name__ == "__main__":
    raise SystemExit(main())
