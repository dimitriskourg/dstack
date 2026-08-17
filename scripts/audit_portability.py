#!/usr/bin/env python3
"""Audit dstack portable skills and Phase 1 adapter invariants."""

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
ADAPTERS = ROOT / "adapters"

CAPABILITIES = {
    "explore",
    "implement",
    "review",
    "parallel",
    "ask_user",
    "verify",
    "model_role",
    "agents.spawn",
    "agents.wait",
    "agents.follow_up",
    "agents.interrupt",
    "agents.collect",
    "agents.isolation",
    "session.history",
    "session.transcript",
    "runtime.wake",
}
MODEL_ROLES = {
    "fast-explorer",
    "feature-worker",
    "bug-worker",
    "deep-judgment",
    "skeptical-reviewer",
    "independent-judge",
}
ADAPTER_NAMES = {"codex", "cursor", "claude-code", "generic"}
STATUSES = {"enforced", "native", "advisory", "approval-required", "unavailable"}
REQUIRED_SKILLS = {
    "architect", "arena", "automate-me", "blast-radius", "bro", "comment-sicko",
    "create-verification-skill", "dstack-mode", "figure-it-out", "how",
    "interrogate", "maintain-verification-skill", "no-comments", "recall",
    "reflect", "setup-dstack", "show-me-your-work", "swarm", "tdd", "teach",
    "technical-writing", "typescript-best-practices", "unslop", "why",
    "principle-boundary-discipline", "principle-build-the-lever",
    "principle-encode-lessons-in-structure", "principle-exhaust-the-design-space",
    "principle-experience-first", "principle-fix-root-causes",
    "principle-foundational-thinking", "principle-guard-the-context-window",
    "principle-laziness-protocol", "principle-make-operations-idempotent",
    "principle-migrate-callers-then-delete-legacy-apis",
    "principle-minimize-reader-load", "principle-model-the-domain",
    "principle-never-block-on-the-human", "principle-outcome-oriented-execution",
    "principle-prove-it-works", "principle-redesign-from-first-principles",
    "principle-separate-before-serializing-shared-state",
    "principle-sequence-verifiable-units", "principle-subtract-before-you-add",
    "principle-type-system-discipline",
}

LEAKAGE_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = (
    ("provider name", re.compile(r"\b(?:Cursor|Codex|Claude Code)\b", re.I)),
    ("provider helper schema", re.compile(r"\b(?:subagent_type|run_in_background|readonly)\s*[:=]", re.I)),
    ("provider skill path", re.compile(r"(?:~|\$HOME)/\.(?:cursor|codex|claude)/", re.I)),
    ("concrete model slug", re.compile(r"\b(?:gpt-\d|grok-|claude-(?:opus|sonnet|haiku|fable))", re.I)),
    ("private transcript layout", re.compile(r"\bagent-transcripts\b|Application Support/Cursor", re.I)),
    ("legacy dstack brand", re.compile(r"\b(?:pstack|ystack|poteto(?:-mode)?)\b", re.I)),
)
ASSET_REF = re.compile(r"(?<![A-Za-z0-9_.-])((?:references|scripts|assets)/[A-Za-z0-9_./-]+)")
CAPABILITY_REF = re.compile(r"`(" + "|".join(re.escape(item) for item in sorted(CAPABILITIES, key=len, reverse=True)) + r")`")
MODEL_ROLE_REF = re.compile(r"`model_role:[a-z0-9-]+`")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SIBLING_SKILL_REF = re.compile(r"`(\.\./[a-z0-9-]+/SKILL\.md)`")


@dataclass(frozen=True)
class Finding:
    path: str
    message: str
    line: Optional[int] = None

    def render(self) -> str:
        location = self.path if self.line is None else "{}:{}".format(self.path, self.line)
        return "ERROR: {}: {}".format(location, self.message)


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


def check_skill(skill_dir: Path) -> List[Finding]:
    findings: List[Finding] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [Finding(relative(skill_dir), "missing SKILL.md")]

    try:
        fields, body = parse_frontmatter(skill_file)
    except ValueError as exc:
        return [Finding(relative(skill_file), str(exc))]

    if set(fields) != {"name", "description"}:
        findings.append(Finding(relative(skill_file), "frontmatter must contain only name and description"))
    if fields.get("name") != skill_dir.name:
        findings.append(Finding(relative(skill_file), "frontmatter name must match the skill directory"))
    if not fields.get("description"):
        findings.append(Finding(relative(skill_file), "frontmatter description is required"))

    package_texts: List[Tuple[Path, str]] = []
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".toml", ".json", ".py", ".sh", ".ts", ".js"}:
            text = path.read_text(encoding="utf-8")
            package_texts.append((path, text))
            for line_number, line in enumerate(text.splitlines(), 1):
                for label, pattern in LEAKAGE_PATTERNS:
                    if pattern.search(line):
                        findings.append(Finding(relative(path), label, line_number))

    used_capabilities: Set[str] = set()
    fallback_capabilities: Set[str] = set()
    for _, text in package_texts:
        used_capabilities.update(CAPABILITY_REF.findall(text))
        if MODEL_ROLE_REF.search(text):
            used_capabilities.add("model_role")
    for line in body.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0].startswith("`") or not cells[0].endswith("`"):
            continue
        capability = cells[0][1:-1]
        fallback = cells[-1]
        if capability in CAPABILITIES and fallback not in {"", "-", "none"}:
            fallback_capabilities.add(capability)
    for capability in sorted(used_capabilities - fallback_capabilities):
        findings.append(Finding(relative(skill_file), "capability {!r} has no explicit fallback row".format(capability)))

    for path, text in package_texts:
        for line_number, line in enumerate(text.splitlines(), 1):
            for reference in ASSET_REF.findall(line):
                reference = reference.rstrip(".,:;)")
                target = skill_dir / reference
                if not target.exists():
                    findings.append(Finding(relative(path), "missing referenced asset {!r}".format(reference), line_number))
            for reference in SIBLING_SKILL_REF.findall(line):
                if not (skill_dir / reference).resolve().is_file():
                    findings.append(Finding(relative(path), "missing sibling skill {!r}".format(reference), line_number))
            for reference in MARKDOWN_LINK.findall(line):
                reference = reference.split("#", 1)[0]
                if not reference or reference.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if "<" in reference or "{" in reference or reference in {"url", "URL", "path"}:
                    continue
                if not (path.parent / reference).resolve().exists():
                    findings.append(Finding(relative(path), "missing markdown link target {!r}".format(reference), line_number))
    return findings


def parse_adapter(path: Path) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    root: Dict[str, str] = {}
    capabilities: Dict[str, Dict[str, str]] = {}
    section: Optional[str] = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^\[capabilities\.(?:"([^"]+)"|([A-Za-z0-9_.-]+))\]$', line)
        if match:
            section = match.group(1) or match.group(2)
            capabilities[section] = {}
            continue
        pair = re.match(r'^([A-Za-z_]+)\s*=\s*(?:"([^"]*)"|(\d+))$', line)
        if not pair:
            raise ValueError("unsupported TOML line: {}".format(raw))
        key = pair.group(1)
        value = pair.group(2) if pair.group(2) is not None else pair.group(3)
        if section is None:
            root[key] = value
        else:
            capabilities[section][key] = value
    return root, capabilities


def parse_profiles(path: Path) -> Tuple[Optional[str], Dict[str, str]]:
    version: Optional[str] = None
    roles: Dict[str, str] = {}
    current: Optional[str] = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^\[roles\.([A-Za-z0-9-]+)\]$", line)
        if match:
            current = match.group(1)
            continue
        if line.startswith("schema_version"):
            version = line.split("=", 1)[1].strip()
            continue
        match = re.match(r'^model\s*=\s*"([^"]+)"$', line)
        if match and current:
            roles[current] = match.group(1)
            continue
        raise ValueError("unsupported TOML line: {}".format(raw))
    return version, roles


def check_adapters() -> List[Finding]:
    findings: List[Finding] = []
    actual = {path.name for path in ADAPTERS.iterdir() if path.is_dir()} if ADAPTERS.is_dir() else set()
    for missing in sorted(ADAPTER_NAMES - actual):
        findings.append(Finding("adapters/{}".format(missing), "missing adapter"))
    for unexpected in sorted(actual - ADAPTER_NAMES):
        findings.append(Finding("adapters/{}".format(unexpected), "unexpected Phase 1 adapter"))

    for name in sorted(ADAPTER_NAMES & actual):
        directory = ADAPTERS / name
        for filename in ("capabilities.toml", "instructions.md", "profiles.toml"):
            if not (directory / filename).is_file():
                findings.append(Finding(relative(directory / filename), "missing adapter file"))
        capabilities_file = directory / "capabilities.toml"
        profiles_file = directory / "profiles.toml"
        if not capabilities_file.is_file() or not profiles_file.is_file():
            continue
        try:
            root, capabilities = parse_adapter(capabilities_file)
        except ValueError as exc:
            findings.append(Finding(relative(capabilities_file), str(exc)))
            continue
        if root.get("schema_version") != "1" or root.get("id") != name or not root.get("display_name"):
            findings.append(Finding(relative(capabilities_file), "invalid adapter identity or schema version"))
        for missing in sorted(CAPABILITIES - set(capabilities)):
            findings.append(Finding(relative(capabilities_file), "missing capability {!r}".format(missing)))
        for extra in sorted(set(capabilities) - CAPABILITIES):
            findings.append(Finding(relative(capabilities_file), "unknown capability {!r}".format(extra)))
        for capability, values in sorted(capabilities.items()):
            if values.get("status") not in STATUSES:
                findings.append(Finding(relative(capabilities_file), "capability {!r} has invalid status".format(capability)))
            if not values.get("fallback"):
                findings.append(Finding(relative(capabilities_file), "capability {!r} has no fallback".format(capability)))
        try:
            version, roles = parse_profiles(profiles_file)
        except ValueError as exc:
            findings.append(Finding(relative(profiles_file), str(exc)))
            continue
        if version != "1":
            findings.append(Finding(relative(profiles_file), "invalid profile schema version"))
        if set(roles) != MODEL_ROLES:
            findings.append(Finding(relative(profiles_file), "profiles must define exactly the semantic model roles"))
        for role, model in roles.items():
            if not model:
                findings.append(Finding(relative(profiles_file), "role {!r} has an empty model binding".format(role)))
    return findings


def check_schemas() -> List[Finding]:
    findings: List[Finding] = []
    for name in ("adapter.schema.json", "profiles.schema.json", "config.schema.json"):
        path = ROOT / "schemas" / name
        if not path.is_file():
            findings.append(Finding(relative(path), "missing schema"))
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            findings.append(Finding(relative(path), "invalid JSON schema: {}".format(exc)))
            continue
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            findings.append(Finding(relative(path), "schema must use JSON Schema draft 2020-12"))
    return findings


def run(skills_root: Path = SKILLS, include_adapters: bool = True) -> List[Finding]:
    findings: List[Finding] = []
    if not skills_root.is_dir():
        return [Finding(relative(skills_root), "skills directory is missing")]
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if skills_root.resolve() == SKILLS.resolve():
        actual = {path.name for path in skill_dirs}
        for missing in sorted(REQUIRED_SKILLS - actual):
            findings.append(Finding("skills/{}".format(missing), "missing required migrated skill"))
        for alias in sorted({"poteto-mode", "setup-pstack", "pstack"} & actual):
            findings.append(Finding("skills/{}".format(alias), "legacy alias is forbidden"))
    for skill_dir in skill_dirs:
        findings.extend(check_skill(skill_dir))
    if include_adapters:
        findings.extend(check_adapters())
        findings.extend(check_schemas())
    return findings


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=SKILLS)
    parser.add_argument("--skills-only", action="store_true")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    findings = run(args.skills_root, include_adapters=not args.skills_only)
    for finding in findings:
        print(finding.render())
    print("dstack portability audit: {} error(s)".format(len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
