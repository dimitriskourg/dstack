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
REQUIRED_SKILLS = {
    "architect", "arena", "automate-me", "blast-radius", "bro", "comment-sicko",
    "control-cli", "control-ui", "create-verification-skill", "deslop", "dstack-mode",
    "figure-it-out", "how", "interrogate", "maintain-verification-skill", "no-comments",
    "recall", "reflect", "setup-dstack", "show-me-your-work", "swarm", "tdd", "teach",
    "technical-writing", "typescript-best-practices", "unslop", "why",
    "principle-boundary-discipline", "principle-build-the-lever",
    "principle-encode-lessons-in-structure", "principle-exhaust-the-design-space",
    "principle-experience-first", "principle-fix-root-causes",
    "principle-foundational-thinking", "principle-guard-the-context-window",
    "principle-laziness-protocol", "principle-make-operations-idempotent",
    "principle-migrate-callers-then-delete-legacy-apis", "principle-minimize-reader-load",
    "principle-model-the-domain", "principle-never-block-on-the-human",
    "principle-outcome-oriented-execution", "principle-prove-it-works",
    "principle-redesign-from-first-principles",
    "principle-separate-before-serializing-shared-state",
    "principle-sequence-verifiable-units", "principle-subtract-before-you-add",
    "principle-type-system-discipline",
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
ASSET_DIRECTORIES = ("references", "scripts", "assets")
ASSET_REF = re.compile(r"(?<![A-Za-z0-9_.-])((?:references|scripts|assets)/[A-Za-z0-9_./-]+)")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SIBLING_SKILL_REF = re.compile(r"`(\.\./[a-z0-9-]+/SKILL\.md)`")
SKILL_CALL = re.compile(r"Call the Skill tool with `([a-z0-9-]+)`\.")
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
    if fields.get("disable-model-invocation") not in {None, "true"}:
        findings.append(Finding(relative(skill_file), "disable-model-invocation must be true or omitted"))
    if skill_dir.name in CONFIG_DEPENDENT_SKILLS:
        if "~/.dstack/config.json" not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must name the fixed config path"))
        if "hosts[<active-harness>]" not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must select the active harness entry directly"))
        if "stop and name the exact problem" not in body or "Tell the user to invoke `setup-dstack` explicitly." not in body:
            findings.append(Finding(relative(skill_file), "config-dependent skill must fail closed with setup-dstack guidance"))
        if skill_dir.name not in {"automate-me", "recall"} and "concrete model and effort pair" not in body:
            findings.append(Finding(relative(skill_file), "profile-consuming skill must require a concrete model and effort pair"))
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
                if not target or target.startswith(("http://", "https://", "mailto:", "#")) or "<" in target or target in {"url", "URL", "path"}:
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
