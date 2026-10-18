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
CONFIG_DEPENDENT_SKILLS = {
    "architect", "arena", "automate-me", "dstack-mode", "how", "interrogate",
    "recall", "reflect", "show-me-your-work", "swarm", "why",
}
TRANSCRIPT_CONFIG_SKILLS = {"automate-me", "dstack-mode", "recall", "reflect", "show-me-your-work"}
CANONICAL_HOST_IDS = {"codex", "claude", "cursor"}
REQUIRED_SKILLS = {
    "architect", "arena", "automate-me", "benchmark-checklist", "blast-radius", "bro",
    "comment-sicko", "control-cli", "control-ui", "correct", "create-verification-skill",
    "deslop", "dstack-help", "dstack-mode",
    "figure-it-out", "how", "in-your-own-words", "interrogate", "ketchup", "maintain-verification-skill", "no-comments",
    "recall", "reflect", "setup-dstack", "sharpen", "show-me-your-work", "swarm", "tdd", "teach",
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
    "apple-dev-cleanup", "authoring-a-skill", "babysit", "bug-fix", "eval",
    "feature", "hillclimb", "investigation", "multi-phase-plan", "opening-a-pr",
    "pause-safely", "perf-issue", "prototype", "refactoring", "runtime-forensics",
    "session-pickup", "trace-forensics", "visual-parity",
}
EXCLUDED_DSTACK_PLAYBOOKS = {
    "autonomous-run", "autopilot-full", "autopilot-stack", "shipping",
    "worktree-cleanup",
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
)
REQUIRED_FRONTMATTER = {"name", "description"}
OPTIONAL_FRONTMATTER = {"disable-model-invocation"}
CODEX_SIDECAR = Path("agents") / "openai.yaml"
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SKILL_NAME_LENGTH = 64
ASSET_DIRECTORIES = ("references", "scripts", "assets")
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
    guide = root / "docs" / "guide"
    if guide.is_dir():
        paths.extend(sorted(path for path in guide.rglob("*.md") if path.is_file()))
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
    if skill_dir.name in CONFIG_DEPENDENT_SKILLS:
        if "~/.dstack/config.json" not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must name the fixed config path"))
        if "hosts[<active-harness>]" not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must select the active harness entry directly"))
        if not CANONICAL_HOST_IDS <= set(re.findall(r"`([a-z]+)`", body)) or "system-provided product identity" not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must derive a canonical harness id"))
        if "invent an alias" not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must reject harness aliases"))
        if skill_dir.name in TRANSCRIPT_CONFIG_SKILLS:
            if "repositories[<canonical-repository-root>]" not in body:
                findings.append(Finding(relative(skill_file), "transcript skill must select the canonical repository entry"))
            if "`repository_root` exactly matches" not in body:
                findings.append(Finding(relative(skill_file), "transcript skill must verify the repository entry identity"))
            if "git rev-parse --git-common-dir" not in body:
                findings.append(Finding(relative(skill_file), "transcript skill must accept linked worktrees via git common directory"))
            if "configure.py resolve" not in body:
                findings.append(Finding(relative(skill_file), "transcript skill must resolve the repository entry with configure.py resolve"))
        if "stop and name the exact problem" not in body or "Tell the user to invoke `setup-dstack` explicitly." not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must fail closed with setup-dstack guidance"))
        if skill_dir.name not in {"automate-me", "recall"}:
            if "concrete model and effort pair" not in body:
                findings.append(Finding(relative(skill_file), "profile-consuming skill must require a concrete model and effort pair"))
            if "`worker_binding`" not in body or not {"`spawn-arguments`", "`worker-definitions`"} <= set(re.findall(r"`[a-z-]+`", body)):
                findings.append(Finding(relative(skill_file), "profile-consuming skill must name the worker_binding mechanisms"))
            if not re.search(r"\b(?:never|do not|must not)\b[^.\n]{0,80}\bsession effort\b", body, re.IGNORECASE):
                findings.append(Finding(relative(skill_file), "profile-consuming skill must forbid inheriting session effort"))
    findings.extend(check_sidecar(skill_dir, "disable-model-invocation" in fields))

    package_texts: List[Tuple[Path, str]] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ts", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        package_texts.append((path, text))
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in LEAKAGE_PATTERNS:
                if pattern.search(line):
                    if label == "provider name" and all(host in line.lower() for host in CANONICAL_HOST_IDS):
                        continue
                    findings.append(Finding(relative(path), label, line_number))
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
        for asset in sorted(path for path in root.rglob("*") if path.is_file()):
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


def check_structure() -> List[Finding]:
    findings: List[Finding] = []
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
    profile_properties = value.get("properties", {}).get("hosts", {}).get("additionalProperties", {}).get("properties", {}).get("profiles", {}).get("properties", {})
    if set(profile_properties) != PROFILES:
        findings.append(Finding(relative(schema), "config must define exactly the four supported profiles"))
    reserved = value.get("$defs", {}).get("modelIdentifier", {}).get("not", {}).get("enum", [])
    if set(reserved) != {"auto", "inherit-parent"}:
        findings.append(Finding(relative(schema), "config must reject automatic and parent-inheritance binding aliases"))
    host_entry = value.get("properties", {}).get("hosts", {}).get("additionalProperties", {})
    if "worker_binding" not in set(host_entry.get("required", [])):
        findings.append(Finding(relative(schema), "each host entry must require a worker binding"))
    host_ids = value.get("properties", {}).get("hosts", {}).get("propertyNames", {}).get("enum", [])
    if set(host_ids) != CANONICAL_HOST_IDS:
        findings.append(Finding(relative(schema), "config must define exactly the three canonical harness ids"))
    if "repositories" not in set(host_entry.get("required", [])):
        findings.append(Finding(relative(schema), "each host entry must require repository-scoped configuration"))
    worker_binding = value.get("$defs", {}).get("workerBinding", {})
    if set(worker_binding.get("required", [])) != {"mechanism", "definitions_directory", "pair_encoding"}:
        findings.append(Finding(relative(schema), "worker binding must require mechanism, directory, and pair encoding"))
    mechanisms = worker_binding.get("properties", {}).get("mechanism", {}).get("enum", [])
    if set(mechanisms) != {"spawn-arguments", "worker-definitions"}:
        findings.append(Finding(relative(schema), "config must define exactly the two supported worker binding mechanisms"))
    encodings = worker_binding.get("properties", {}).get("pair_encoding", {}).get("enum", [])
    if set(encodings) != {"sibling-fields", "model-brackets", None}:
        findings.append(Finding(relative(schema), "config must define exactly the two supported pair encodings"))

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
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ts", ".js"}:
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
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".json", ".py", ".sh", ".ts", ".js"}:
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
