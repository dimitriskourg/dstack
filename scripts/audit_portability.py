#!/usr/bin/env python3
"""Audit dstack portable skill packages and configuration invariants."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
PROFILES = {"fast-explorer", "feature-worker", "bug-worker", "skeptical-reviewer"}
CONFIG_SKILL = "dstack-config"
CONFIG_CALL = "Call the Skill tool with `dstack-config`."
CONFIG_CALLERS = {
    "arena", "dstack-mode", "how", "interrogate",
    "recall", "reflect", "swarm", "why",
}
CONFIG_OWNERS = {CONFIG_SKILL, "setup-dstack"}
CONFIG_PROCEDURE_MARKERS = (
    "hosts[<active-harness>]", "repositories[<canonical-repository-root>]",
    "configure.py", "invalid_bindings", "transcripts_directory",
    "system-provided product identity", "separate spawn arguments", "already carries effort",
)
USER_GUIDE_CONFIG_MARKERS = ("~/.dstack/config.json", "--git-common-dir")
USER_GUIDE_SKILL = "dstack-help"
CANONICAL_HOST_IDS = {"codex", "claude", "cursor"}
REQUIRED_SKILLS = {
    "architect", "arena", "blast-radius", "bro",
    "comment-sicko", "control-ui", "correct", "create-formal-verification-skill", "create-verification-skill", "maintain-formal-verification-skill",
    "deslop", "dstack-config", "dstack-help", "dstack-mode",
    "how", "in-your-own-words", "interrogate", "ketchup", "ketchup-video", "maintain-verification-skill", "no-comments",
    "recall", "reflect", "setup-dstack", "sharpen", "statechart", "swarm", "tdd", "teach",
    "technical-writing", "typescript-best-practices", "unslop", "why",
    "principle-attack-the-premise", "principle-boundary-discipline",
    "principle-build-the-lever",
    "principle-encode-lessons-in-structure", "principle-exhaust-the-design-space",
    "principle-explain-the-number",
    "principle-experience-first", "principle-fix-root-causes",
    "principle-foundational-thinking", "principle-guard-the-context-window",
    "principle-laziness-protocol", "principle-make-operations-idempotent",
    "principle-migrate-callers-then-delete-legacy-apis", "principle-minimize-reader-load",
    "principle-model-the-domain", "principle-never-block-on-the-human",
    "principle-outcome-oriented-execution", "principle-prove-it-works",
    "principle-redesign-from-first-principles",
    "principle-separate-before-serializing-shared-state",
    "principle-sequence-verifiable-units", "principle-subtract-before-you-add",
    "principle-test-behavior-not-implementation",
    "principle-type-system-discipline",
}
REQUIRED_DSTACK_PLAYBOOKS = {
    "authoring-a-skill", "babysit", "bug-fix",
    "feature", "investigation", "opening-a-pr",
    "pause-safely", "prototype", "refactoring",
    "session-pickup",
}
REMOVED_DOCS = ("DIFFERENCES.md", "KNOWN_ISSUES.md", "docs")
SYNC_PIN = re.compile(r"^Pinned: pstack \S+, commit `[0-9a-f]{40}`\.$", re.M)
EXCLUDED_DSTACK_PLAYBOOKS = {
    "autonomous-run", "autopilot-full", "autopilot-stack", "eval",
    "hillclimb", "multi-phase-plan", "orchestrate", "perf-issue", "runtime-forensics", "shipping",
    "trace-forensics", "visual-parity", "worktree-cleanup",
}
LEAKAGE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("provider name", re.compile(r"\b(?:Cursor|Codex|Claude Code)\b", re.I)),
    ("provider helper schema", re.compile(r"\b(?:subagent_type|run_in_background|readonly)`?\s*[:=]", re.I)),
    ("provider configuration path", re.compile(r"(?:~|\$HOME)/\.(?:cursor|codex|claude)/", re.I)),
    ("concrete model slug", re.compile(r"\b(?:gpt-\d|grok-|claude-(?:opus|sonnet|haiku|fable))", re.I)),
    ("private transcript layout", re.compile(r"\bagent-transcripts\b|Application Support/Cursor", re.I)),
    ("legacy brand", re.compile(r"\b(?:pstack|ystack|poteto(?:-mode)?)\b", re.I)),
    ("config path override", re.compile(r"\bDSTACK_HOME\b|--dstack-home")),
    ("host selection override", re.compile(r"\bhost_override\b")),
    (
        "retired worker binding",
        re.compile(r"\bworker_binding\b|\bworker-definitions\b|\bspawn-arguments\b|\bpair_encoding\b|"
                   r"\bdefinitions_directory\b|\bdstack-<profile>|\bworker_bindings\.py\b"),
    ),
)
HOST_BINDINGS = {"codex": "pairHost", "claude": "pairHost", "cursor": "cursorHost"}
HOST_ENTRY_FIELDS = {"profiles", "invalid_bindings", "repositories"}
REQUIRED_FRONTMATTER = {"name", "description"}
OPTIONAL_FRONTMATTER = {"disable-model-invocation"}
CODEX_SIDECAR = Path("agents") / "openai.yaml"
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SKILL_NAME_LENGTH = 64
ASSET_DIRECTORIES = ("references", "scripts", "assets")
IGNORED_ASSET_NAMES = {"__pycache__", "node_modules"}
IGNORED_ASSET_SUFFIXES = {".pyc", ".pyo"}
ASSET_REF = re.compile(r"(?<![A-Za-z0-9_.-])((?:references|scripts|assets)/[A-Za-z0-9_./-]+)")
MARKDOWN_LINK = re.compile(r"\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
DOC_CLAIM = re.compile(
    r"\b(?:(?P<whole>all|has|of|ships|the|with) )?(?P<word>\d+|[a-z]+(?:-[a-z]+)?) (?P<short>short )?(?P<noun>skills|principles|playbooks)\b",
    re.I,
)
DOC_SLASH = re.compile(r"(?:^|(?<=[\s`(|\"'>]))/([a-z][a-z0-9-]*)(?![\w/<\-])", re.M)
SMALL_COUNT_WORDS = (
    "zero one two three four five six seven eight nine ten eleven "
    "twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
).split()
TENS_COUNT_WORDS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SIBLING_SKILL_REF = re.compile(r"`(\.\./[a-z0-9-]+/SKILL\.md)`")
SKILL_CALL = re.compile(r"Call the Skill tool with `([a-z0-9-]+)`\.")
KEBAB_DROP_PUNCTUATION = re.compile(r"[^A-Za-z0-9\s-]")
KEBAB_WHITESPACE = re.compile(r"\s+")
PRINCIPLE_INDEX_ENTRY = re.compile(
    r"^- \*\*(?P<title>.+?)\.?\*\*(?: \(\*\*(?P<name>[a-z0-9-]+)\*\*\))?\.?"
)
PLAYBOOK_INDEX_ENTRY = re.compile(r"^- \*\*(?P<title>.+?)\.\*\*")
PLAYBOOK_EXPLICIT_FILE = re.compile(r"(?:File:\s+)?`playbooks/([a-z0-9-]+)\.md`")
LEGACY_SKILL_DIRECTIVE = re.compile(
    r"\b(?:run|apply|invoke|route through|route to|hand to|use)\s+"
    r"(?:the\s+)?(?:\*\*)?(" + "|".join(sorted(REQUIRED_SKILLS, key=len, reverse=True)) + r")"
    r"(?:\*\*)?\s+skill\b",
    re.I,
)


@dataclass(frozen=True)
class Finding:
    path: str
    message: str
    line: Optional[int] = None

    def render(self) -> str:
        location = self.path if self.line is None else "{}:{}".format(self.path, self.line)
        return "ERROR: {}: {}".format(location, self.message)


def count_word_to_number(word: str) -> Optional[int]:
    if word.isdigit():
        return int(word)
    parts = word.lower().split("-")
    if len(parts) == 1 and parts[0] in SMALL_COUNT_WORDS:
        return SMALL_COUNT_WORDS.index(parts[0])
    if len(parts) == 2:
        tens, unit = parts
        ones = SMALL_COUNT_WORDS.index(unit) if unit in SMALL_COUNT_WORDS else -1
        if tens in TENS_COUNT_WORDS and TENS_COUNT_WORDS.index(tens) > 1 and 0 <= ones < 10:
            return TENS_COUNT_WORDS.index(tens) * 10 + ones
    return None


def heading_anchors(text: str) -> Set[str]:
    seen: Dict[str, int] = {}
    found: Set[str] = set()
    fenced = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if not heading:
            continue
        plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading.group(1))
        plain = re.sub(r"[`*]", "", plain)
        slug = re.sub(r"[^\w\s_-]", "", plain.strip().lower(), flags=re.UNICODE)
        slug = re.sub(r"\s", "-", slug)
        repeat = seen.get(slug, 0)
        seen[slug] = repeat + 1
        found.add("{}-{}".format(slug, repeat) if repeat else slug)
    return found


def documentation_paths(root: Path) -> List[Path]:
    paths: List[Path] = []
    readme = root / "README.md"
    if readme.is_file():
        paths.append(readme)
    help_root = root / "skills" / "dstack-help"
    if help_root.is_dir():
        paths.extend(sorted(path for path in help_root.rglob("*.md") if path.is_file()))
    return paths


def check_docs_vs_tree(
    root: Path,
    skill_names: Set[str],
    playbook_stems: Set[str],
) -> List[Finding]:
    """Fail when user-facing docs drift from the skill and playbook tree.

    Adapted from pstack's docs-vs-tree check. dstack has no agent wrappers and
    no hardcoded model catalog, so those legs are omitted. README is not a
    full skill catalog, so missing table rows are not errors.
    """

    principles = {name for name in skill_names if name.startswith("principle-")}
    commands = skill_names - principles
    expected = {
        "skills": {len(skill_names), len(commands)},
        "principles": {len(principles)},
        "playbooks": {len(playbook_stems)},
    }
    findings: List[Finding] = []
    for path in documentation_paths(root):
        text = path.read_text(encoding="utf-8")
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        for match in DOC_CLAIM.finditer(text):
            claimed = count_word_to_number(match.group("word"))
            kind = "principles" if match.group("short") else match.group("noun").lower()
            if (match.group("whole") or match.group("short")) and claimed is not None and claimed not in expected[kind]:
                findings.append(Finding(
                    rel,
                    'says "{}", but the tree has {}'.format(
                        match.group(0),
                        " or ".join(str(value) for value in sorted(expected[kind])),
                    ),
                    text[: match.start()].count("\n") + 1,
                ))
        for match in DOC_SLASH.finditer(text):
            name = match.group(1)
            if name not in skill_names:
                findings.append(Finding(
                    rel,
                    "names /{}, which no dstack skill provides".format(name),
                    text[: match.start()].count("\n") + 1,
                ))
        for line_number, line in enumerate(text.splitlines(), 1):
            for reference in MARKDOWN_LINK.findall(line):
                href = reference
                if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I) or href.startswith("#") or href in {"url", "URL", "path"}:
                    continue
                target, _, anchor = href.partition("#")
                if not target:
                    resolved = path
                else:
                    resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    findings.append(Finding(rel, "missing markdown link target {!r}".format(href), line_number))
                    continue
                if anchor and resolved.suffix.lower() == ".md":
                    try:
                        relative_target = resolved.relative_to(root).as_posix()
                    except ValueError:
                        relative_target = resolved.as_posix()
                    if anchor not in heading_anchors(resolved.read_text(encoding="utf-8")):
                        findings.append(Finding(
                            rel,
                            "links to {}, but {} has no heading with that anchor".format(href, relative_target),
                            line_number,
                        ))
    return findings


def kebab_from_title(title: str) -> str:
    """Turn a principle or playbook title into a kebab-case name.

    Hyphens stay. Other punctuation is dropped. Remaining whitespace becomes
    hyphens. This matches the naming-by-convention instruction in dstack-mode.
    """

    text = KEBAB_DROP_PUNCTUATION.sub("", title)
    text = KEBAB_WHITESPACE.sub("-", text.strip())
    return re.sub(r"-{2,}", "-", text).strip("-").lower()


def resolve_principle_index(body: str) -> List[Tuple[str, str, int]]:
    """Return (title, skill directory name, line number) for each principle entry."""

    entries: List[Tuple[str, str, int]] = []
    in_principles = False
    for line_number, line in enumerate(body.splitlines(), 1):
        if line.startswith("## "):
            in_principles = line == "## Principles"
            continue
        if not in_principles:
            continue
        match = PRINCIPLE_INDEX_ENTRY.match(line)
        if not match:
            continue
        title = match.group("title").rstrip(".")
        name = match.group("name") or "principle-" + kebab_from_title(title)
        entries.append((title, name, line_number))
    return entries


def check_mode_index(
    body: str,
    skill_names: Set[str],
    playbook_stems: Set[str],
    path: str,
) -> List[Finding]:
    findings: List[Finding] = []
    for title, name, line_number in resolve_principle_index(body):
        if name not in skill_names:
            findings.append(Finding(
                path,
                "principle title {!r} does not resolve to an existing skill ({})".format(title, name),
                line_number,
            ))
    resolved_playbooks: Set[str] = set()
    for title, stem, line_number in resolve_playbook_index(body):
        resolved_playbooks.add(stem)
        if stem not in playbook_stems:
            findings.append(Finding(
                path,
                "playbook title {!r} does not resolve to an existing playbook ({})".format(title, stem),
                line_number,
            ))
        if stem in EXCLUDED_DSTACK_PLAYBOOKS:
            findings.append(Finding(
                path,
                "playbook title {!r} resolves to excluded playbook {!r}".format(title, stem),
                line_number,
            ))
    for missing in sorted(REQUIRED_DSTACK_PLAYBOOKS - resolved_playbooks):
        findings.append(Finding(
            path,
            "supported playbook {!r} is not referenced by a resolvable title".format(missing),
        ))
    return findings


def resolve_playbook_index(body: str) -> List[Tuple[str, str, int]]:
    """Return (title, playbook stem, line number) for each playbook entry."""

    entries: List[Tuple[str, str, int]] = []
    in_playbooks = False
    for line_number, line in enumerate(body.splitlines(), 1):
        if line.startswith("## "):
            in_playbooks = line == "## Playbooks"
            continue
        if not in_playbooks:
            continue
        match = PLAYBOOK_INDEX_ENTRY.match(line)
        if not match:
            continue
        title = match.group("title")
        explicit = PLAYBOOK_EXPLICIT_FILE.search(line)
        stem = explicit.group(1) if explicit else kebab_from_title(title)
        entries.append((title, stem, line_number))
    return entries


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_frontmatter(path: Path) -> Tuple[Dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    fields: Dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields, text[end + 5 :]


def check_sidecar(skill_dir: Path, user_invoked: bool) -> List[Finding]:
    sidecar = skill_dir / CODEX_SIDECAR
    if not sidecar.is_file():
        return [Finding(relative(sidecar), "missing Codex sidecar")]
    lines = sidecar.read_text(encoding="utf-8").splitlines()
    findings: List[Finding] = []
    for key in ("display_name", "short_description"):
        if not any(line.strip().startswith(key + ":") and line.strip() != key + ":" for line in lines):
            findings.append(Finding(relative(sidecar), "sidecar interface.{} is required".format(key)))
    denies_implicit = any(line.strip().replace(" ", "") == "allow_implicit_invocation:false" for line in lines)
    if user_invoked != denies_implicit:
        findings.append(Finding(relative(sidecar), "sidecar invocation policy disagrees with SKILL.md"))
    return findings


def is_ignored_skill_path(path: Path) -> bool:
    return any(part in IGNORED_ASSET_NAMES for part in path.parts)


def is_package_asset(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() in IGNORED_ASSET_SUFFIXES:
        return False
    return not is_ignored_skill_path(path)


def reference_forms(source_dir: Path, skill_dir: Path, target: Path) -> Set[str]:
    forms = {target.relative_to(skill_dir).as_posix()}
    try:
        forms.add(target.relative_to(source_dir).as_posix())
    except ValueError:
        pass
    return forms


def mentions_directory(text: str, source_dir: Path, skill_dir: Path, target: Path) -> bool:
    return any(
        re.search(re.escape(form + "/") + r"(?![\w./-])", text)
        for form in reference_forms(source_dir, skill_dir, target)
    )


def check_config_procedure(skill_file: Path, body: str) -> List[Finding]:
    required = (
        ("~/.dstack/config.json" in body, "config skill must name the fixed config path"),
        ("hosts[<active-harness>]" in body, "config skill must select the active harness entry directly"),
        (
            CANONICAL_HOST_IDS <= set(re.findall(r"`([a-z]+)`", body)) and "system-provided product identity" in body,
            "config skill must derive a canonical harness id",
        ),
        ("invent an alias" in body, "config skill must reject harness aliases"),
        ("repositories[<canonical-repository-root>]" in body, "config skill must select the canonical repository entry"),
        ("`repository_root` exactly matches" in body, "config skill must verify the repository entry identity"),
        ("git rev-parse --git-common-dir" in body, "config skill must accept linked worktrees via git common directory"),
        ("configure.py resolve" in body, "config skill must resolve the repository entry with configure.py resolve"),
        ("transcripts_directory" in body, "config skill must return the transcripts directory"),
        (
            "stop and name the exact problem" in body and "Tell the user to invoke `setup-dstack` explicitly." in body,
            "config skill must fail closed with setup-dstack guidance",
        ),
        ("concrete model and effort pair" in body, "config skill must require a concrete model and effort pair"),
        (
            "separate spawn arguments" in body and "already carries effort" in body,
            "config skill must state how each host's spawn call takes the profile",
        ),
        (
            bool(re.search(r"\b(?:never|do not|must not)\b[^.\n]{0,80}\bsession effort\b", body, re.IGNORECASE)),
            "config skill must forbid inheriting session effort",
        ),
    )
    return [Finding(relative(skill_file), message) for ok, message in required if not ok]


def check_skill(skill_dir: Path) -> List[Finding]:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [Finding(relative(skill_dir), "missing SKILL.md")]
    try:
        fields, body = parse_frontmatter(skill_file)
    except ValueError as error:
        return [Finding(relative(skill_file), str(error))]
    findings: List[Finding] = []
    present = set(fields)
    if not REQUIRED_FRONTMATTER <= present:
        findings.append(Finding(relative(skill_file), "frontmatter must contain name and description"))
    unsupported = present - REQUIRED_FRONTMATTER - OPTIONAL_FRONTMATTER
    if unsupported:
        findings.append(Finding(relative(skill_file), "unsupported frontmatter key(s): " + ", ".join(sorted(unsupported))))
    if fields.get("name") != skill_dir.name:
        findings.append(Finding(relative(skill_file), "frontmatter name must match the skill directory"))
    if not SKILL_NAME.fullmatch(skill_dir.name) or len(skill_dir.name) > MAX_SKILL_NAME_LENGTH:
        findings.append(Finding(
            relative(skill_dir),
            "skill directory must be lowercase words joined by hyphens, at most 64 characters",
        ))
    if fields.get("disable-model-invocation") not in {None, "true"}:
        findings.append(Finding(relative(skill_file), "disable-model-invocation must be true or omitted"))
    if skill_dir.name == CONFIG_SKILL:
        findings.extend(check_config_procedure(skill_file, body))
    if skill_dir.name in CONFIG_CALLERS and CONFIG_CALL not in body:
        findings.append(Finding(relative(skill_file), "config-dependent skill must resolve config through dstack-config"))
    findings.extend(check_sidecar(skill_dir, "disable-model-invocation" in fields))

    package_texts: List[Tuple[Path, str]] = []
    for path in sorted(skill_dir.rglob("*")):
        if is_ignored_skill_path(path):
            continue
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ts", ".js", ".mjs"}:
            continue
        text = path.read_text(encoding="utf-8")
        package_texts.append((path, text))
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in LEAKAGE_PATTERNS:
                if pattern.search(line):
                    if label == "provider name" and all(host in line.lower() for host in CANONICAL_HOST_IDS):
                        continue
                    findings.append(Finding(relative(path), label, line_number))
            if skill_dir.name not in CONFIG_OWNERS:
                markers = CONFIG_PROCEDURE_MARKERS
                if skill_dir.name != USER_GUIDE_SKILL:
                    markers += USER_GUIDE_CONFIG_MARKERS
                if any(marker in line for marker in markers):
                    findings.append(Finding(relative(path), "config procedure belongs only in dstack-config", line_number))
            if "Call the Skill tool with" in line:
                calls = SKILL_CALL.findall(line)
                if not calls or line.count("Call the Skill tool with") != len(calls):
                    findings.append(Finding(relative(path), "skill call must use the exact portable phrase", line_number))
            if LEGACY_SKILL_DIRECTIVE.search(line) and "Call the Skill tool with" not in line:
                findings.append(Finding(relative(path), "skill directive must use the Skill tool phrase", line_number))

    for path, text in package_texts:
        in_fence = False
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for reference in ASSET_REF.findall(line):
                reference = reference.rstrip(".,:;)")
                if not (skill_dir / reference).exists():
                    findings.append(Finding(relative(path), "missing referenced asset {!r}".format(reference), line_number))
            if path.suffix.lower() != ".md":
                continue
            for reference in SIBLING_SKILL_REF.findall(line):
                if not (skill_dir / reference).resolve().is_file():
                    findings.append(Finding(relative(path), "missing sibling skill {!r}".format(reference), line_number))
            for reference in MARKDOWN_LINK.findall(line):
                target = reference.split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:", "#")) or target in {"url", "URL", "path"}:
                    continue
                if not (path.parent / target).resolve().exists():
                    findings.append(Finding(relative(path), "missing markdown link target {!r}".format(target), line_number))

    for directory in ASSET_DIRECTORIES:
        root = skill_dir / directory
        if not root.is_dir():
            continue
        for asset in sorted(path for path in root.rglob("*") if is_package_asset(path)):
            sources = [(path, text) for path, text in package_texts if path != asset]
            if any(any(form in text for form in reference_forms(path.parent, skill_dir, asset)) for path, text in sources):
                continue
            containers = [parent for parent in asset.parents if root in parent.parents]
            if any(
                mentions_directory(text, path.parent, skill_dir, container)
                for path, text in sources
                for container in containers
            ):
                continue
            findings.append(Finding(relative(asset), "asset is never referenced by the skill"))
    return findings


def schema_findings(value: Dict) -> List[str]:
    messages: List[str] = []
    definitions = value.get("$defs", {})
    hosts = value.get("properties", {}).get("hosts", {})
    if set(hosts.get("propertyNames", {}).get("enum", [])) != CANONICAL_HOST_IDS:
        messages.append("config must define exactly the three canonical harness ids")
    host_refs = {
        host: entry.get("$ref", "").rpartition("/")[2]
        for host, entry in hosts.get("properties", {}).items()
    }
    if host_refs != HOST_BINDINGS or hosts.get("additionalProperties") is not False:
        messages.append("codex and claude must use pairHost and cursor must use cursorHost")
    for name in sorted(set(HOST_BINDINGS.values())):
        entry = definitions.get(name, {})
        if set(entry.get("required", [])) != HOST_ENTRY_FIELDS or set(entry.get("properties", {})) != HOST_ENTRY_FIELDS:
            messages.append("{} must contain exactly profiles, invalid_bindings, and repositories".format(name))
        if set(entry.get("properties", {}).get("profiles", {}).get("properties", {})) != PROFILES:
            messages.append("{} must define exactly the four supported profiles".format(name))
    for name, fields in (("pairBinding", {"model", "effort"}), ("cursorBinding", {"model"})):
        binding = definitions.get(name, {})
        if set(binding.get("required", [])) != fields or set(binding.get("properties", {})) != fields:
            messages.append("{} must contain exactly {}".format(name, " and ".join(sorted(fields))))
    reserved = definitions.get("modelIdentifier", {}).get("not", {}).get("enum", [])
    if set(reserved) != {"auto", "inherit", "inherit-parent"}:
        messages.append("config must reject automatic and parent-inheritance binding aliases")
    if "workerBinding" in definitions:
        messages.append("retired worker binding must stay absent from the schema")
    return messages


def sync_section(text: str, heading: str) -> Set[str]:
    match = re.search(r"^## {}\n(.*?)(?=^## |\Z)".format(re.escape(heading)), text, re.M | re.S)
    return set(re.findall(r"^- `([^`]+)`", match.group(1), re.M)) if match else set()


def check_sync_file(root: Path) -> List[Finding]:
    path = root / "PSTACK_SYNC.md"
    if not path.is_file():
        return [Finding("PSTACK_SYNC.md", "missing pstack sync contract")]
    text = path.read_text(encoding="utf-8")
    findings: List[Finding] = []
    if not SYNC_PIN.search(text):
        findings.append(Finding("PSTACK_SYNC.md", "must pin a pstack version and full commit"))
    if not re.search(r"^Upstream: repository `cursor/plugins`, subpath `pstack/`", text, re.M):
        findings.append(Finding("PSTACK_SYNC.md", "must record upstream repository cursor/plugins and subpath pstack/"))
    if sync_section(text, "Excluded playbooks") != EXCLUDED_DSTACK_PLAYBOOKS:
        findings.append(Finding("PSTACK_SYNC.md", "excluded playbooks disagree with the audit"))
    for skill in sorted(sync_section(text, "Excluded skills") & {path.name for path in (root / "skills").iterdir()}):
        findings.append(Finding("skills/" + skill, "excluded pstack skill must stay absent"))
    for removed in REMOVED_DOCS:
        if (root / removed).exists():
            findings.append(Finding(removed, "retired document must stay absent; PSTACK_SYNC.md, README.md, and dstack-help replace it"))
    return findings


def check_structure() -> List[Finding]:
    findings: List[Finding] = check_sync_file(ROOT)
    for removed in ("adapters", "contracts"):
        if (ROOT / removed).exists() and any((ROOT / removed).iterdir()):
            findings.append(Finding(removed, "removed portability layer must stay absent"))
    schema = ROOT / "schemas" / "config.schema.json"
    try:
        value = json.loads(schema.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return findings + [Finding(relative(schema), "invalid JSON schema: {}".format(error))]
    if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        findings.append(Finding(relative(schema), "schema must use JSON Schema draft 2020-12"))
    if set(value.get("required", [])) != {"schema_version", "hosts"} or set(value.get("properties", {})) != {"schema_version", "hosts"}:
        findings.append(Finding(relative(schema), "config root must contain only schema_version and hosts"))
    findings.extend(Finding(relative(schema), message) for message in schema_findings(value))

    playbooks = SKILLS / "dstack-mode" / "playbooks"
    actual_playbooks = {path.stem for path in playbooks.glob("*.md")}
    for missing in sorted(REQUIRED_DSTACK_PLAYBOOKS - actual_playbooks):
        findings.append(Finding(relative(playbooks / (missing + ".md")), "missing supported dstack-mode playbook"))
    for excluded in sorted(EXCLUDED_DSTACK_PLAYBOOKS & actual_playbooks):
        findings.append(Finding(relative(playbooks / (excluded + ".md")), "excluded dstack-mode playbook must stay absent"))

    mode_skill = SKILLS / "dstack-mode" / "SKILL.md"
    skill_names = {path.name for path in SKILLS.iterdir() if path.is_dir()}
    if mode_skill.is_file():
        findings.extend(check_mode_index(
            mode_skill.read_text(encoding="utf-8"),
            skill_names,
            actual_playbooks,
            relative(mode_skill),
        ))
    findings.extend(check_docs_vs_tree(ROOT, skill_names, actual_playbooks))

    unsupported_references = {
        "playbooks/{}.md".format(name) for name in EXCLUDED_DSTACK_PLAYBOOKS
    }
    for path in sorted(SKILLS.rglob("*")):
        if is_ignored_skill_path(path):
            continue
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ts", ".js", ".mjs"}:
            continue
        text = path.read_text(encoding="utf-8")
        for reference in sorted(unsupported_references):
            if reference in text:
                findings.append(Finding(relative(path), "reference to excluded playbook {!r}".format(reference)))
        if "git reset --hard" in text:
            findings.append(Finding(relative(path), "destructive hard-reset workflow is forbidden"))
    return findings


def check_invocation_targets(skill_dirs: Iterable[Path]) -> List[Finding]:
    skill_dirs = list(skill_dirs)
    model_disabled: Set[str] = set()
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        try:
            fields, _ = parse_frontmatter(skill_file)
        except ValueError:
            continue
        if fields.get("disable-model-invocation") == "true":
            model_disabled.add(skill_dir.name)

    findings: List[Finding] = []
    for skill_dir in skill_dirs:
        for path in sorted(skill_dir.rglob("*")):
            if is_ignored_skill_path(path):
                continue
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ts", ".js", ".mjs"}:
                continue
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for target in SKILL_CALL.findall(line):
                    if target in model_disabled:
                        findings.append(Finding(
                            relative(path),
                            "model-disabled skill {!r} cannot be used as an internal callee".format(target),
                            line_number,
                        ))
    return findings


def run(skills_root: Path = SKILLS, include_structure: bool = True) -> List[Finding]:
    if not skills_root.is_dir():
        return [Finding(relative(skills_root), "skills directory is missing")]
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    findings: List[Finding] = []
    if skills_root.resolve() == SKILLS.resolve():
        actual = {path.name for path in skill_dirs}
        for missing in sorted(REQUIRED_SKILLS - actual):
            findings.append(Finding("skills/{}".format(missing), "missing required skill"))
        for alias in sorted({"poteto-mode", "setup-pstack", "pstack"} & actual):
            findings.append(Finding("skills/{}".format(alias), "legacy alias is forbidden"))
    for skill_dir in skill_dirs:
        findings.extend(check_skill(skill_dir))
    findings.extend(check_invocation_targets(skill_dirs))
    if include_structure:
        findings.extend(check_structure())
    return findings


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=SKILLS)
    parser.add_argument("--skills-only", action="store_true")
    args = parser.parse_args(list(argv))
    findings = run(args.skills_root, include_structure=not args.skills_only)
    for finding in findings:
        print(finding.render())
    print("dstack portability audit: {} error(s)".format(len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
