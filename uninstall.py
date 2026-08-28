#!/usr/bin/env python3
"""Remove verified dstack skills, or remove dstack completely."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Set


SOURCE_ROOT = Path(__file__).resolve().parent
DSTACK_DIRECTORY = Path("~/.dstack").expanduser()
PROFILES = ("fast-explorer", "feature-worker", "bug-worker", "skeptical-reviewer")
MOUNT_POINT_REPARSE_TAG = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)


class UninstallError(Exception):
    pass


@dataclass(frozen=True)
class Removal:
    kind: str
    path: Path

    def preview(self) -> str:
        return "Would remove {}: {}".format(self.kind, self.path)

    def completed(self) -> str:
        return "Removed {}: {}".format(self.kind, self.path)


def path_exists(path: Path) -> bool:
    return os.path.lexists(str(path))


def is_compatibility_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        return os.lstat(str(path)).st_reparse_tag == MOUNT_POINT_REPARSE_TAG
    except (AttributeError, OSError):
        return False


def skill_identity(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.fullmatch(r"name:\s*['\"]?([a-z0-9-]+)['\"]?", line.strip())
        if match:
            return match.group(1)
    return ""


def bundled_skill_names(source_root: Path) -> List[str]:
    skills_root = source_root / "skills"
    if not skills_root.is_dir():
        raise UninstallError("source skills directory is missing: {}".format(skills_root))
    names = sorted(
        path.name
        for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    if not names:
        raise UninstallError("no skill packages found under {}".format(skills_root))
    return names


def worker_definition_directories(config_path: Path) -> Set[Path]:
    if not config_path.exists():
        return set()
    if not config_path.is_file() or config_path.is_symlink():
        raise UninstallError("expected a regular configuration file: {}".format(config_path))
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UninstallError("cannot read worker definitions from {}: {}".format(config_path, error))

    hosts = config.get("hosts") if isinstance(config, dict) else None
    if not isinstance(hosts, dict):
        raise UninstallError("configuration hosts must be an object: {}".format(config_path))

    directories: Set[Path] = set()
    for host, entry in hosts.items():
        binding = entry.get("worker_binding") if isinstance(entry, dict) else None
        if not isinstance(binding, dict):
            raise UninstallError("host {!r} has no valid worker_binding".format(host))
        if binding.get("mechanism") != "worker-definitions":
            continue
        value = binding.get("definitions_directory")
        if not isinstance(value, str) or not value or not Path(value).expanduser().is_absolute():
            raise UninstallError("host {!r} has no absolute definitions_directory".format(host))
        directories.add(Path(value).expanduser().resolve())
    return directories


def verify_worker_definition(path: Path, profile: str) -> bool:
    if not path_exists(path):
        return False
    if not path.is_file() or path.is_symlink():
        raise UninstallError("expected a regular dstack worker definition: {}".format(path))
    text = path.read_text(encoding="utf-8")
    expected_name = "dstack-{}".format(profile)
    if skill_identity(path) != expected_name or "<!-- dstack-managed-worker: {} -->".format(profile) not in text:
        raise UninstallError("worker definition ownership cannot be verified: {}".format(path))
    return True


def build_removals(
    source_root: Path,
    skills_directory: Path,
    claude_skills_directory: Path,
    dstack_home: Path,
    remove_all: bool,
) -> List[Removal]:
    names = bundled_skill_names(source_root)
    removals: List[Removal] = []

    for name in names:
        skill = skills_directory / name
        link = claude_skills_directory / name
        if path_exists(link):
            if not is_compatibility_link(link):
                raise UninstallError("expected a dstack compatibility link: {}".format(link))
            if link.resolve() != skill.resolve():
                raise UninstallError("compatibility link points outside the dstack install: {}".format(link))
            removals.append(Removal("Claude compatibility link", link))
        if path_exists(skill):
            if not skill.is_dir() or skill.is_symlink():
                raise UninstallError("expected an installed skill directory: {}".format(skill))
            if skill_identity(skill / "SKILL.md") != name:
                raise UninstallError("installed skill ownership cannot be verified: {}".format(skill))
            removals.append(Removal("skill", skill))

    if not remove_all:
        return removals

    config_path = dstack_home / "config.json"
    for directory in sorted(worker_definition_directories(config_path), key=str):
        for profile in PROFILES:
            path = directory / "dstack-{}.md".format(profile)
            if verify_worker_definition(path, profile):
                removals.append(Removal("worker definition", path))

    if path_exists(dstack_home):
        if not dstack_home.is_dir() or dstack_home.is_symlink():
            raise UninstallError("expected a regular dstack configuration directory: {}".format(dstack_home))
        removals.append(Removal("configuration directory", dstack_home))
    return removals


def remove(removal: Removal) -> None:
    path = removal.path
    if is_compatibility_link(path):
        if path.is_symlink():
            path.unlink()
        else:
            os.rmdir(str(path))
    elif path.is_dir():
        shutil.rmtree(str(path))
    else:
        path.unlink()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--skills-only",
        action="store_true",
        help="remove dstack skills and Claude compatibility links, preserving configuration",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        help="remove skills, compatibility links, generated workers, and ~/.dstack",
    )
    result.add_argument("--dry-run", action="store_true", help="show verified removals without changing files")
    result.add_argument("--skills-dir", default="~/.agents/skills", metavar="PATH")
    result.add_argument("--claude-skills-dir", default="~/.claude/skills", metavar="PATH")
    return result


def resolved(value: str) -> Path:
    return Path(value).expanduser().resolve()


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    try:
        removals = build_removals(
            source_root=SOURCE_ROOT,
            skills_directory=resolved(options.skills_dir),
            claude_skills_directory=resolved(options.claude_skills_dir),
            dstack_home=DSTACK_DIRECTORY.resolve(),
            remove_all=options.all,
        )
    except (UninstallError, OSError) as error:
        print("Uninstall stopped before removals: {}".format(error), file=sys.stderr)
        print("No files changed.", file=sys.stderr)
        return 2

    if options.dry_run:
        for removal in removals:
            print(removal.preview())
        print("Uninstall dry run complete: {} removals; no files changed.".format(len(removals)))
        return 0

    completed = 0
    try:
        for removal in removals:
            remove(removal)
            completed += 1
            print(removal.completed())
    except OSError as error:
        print(
            "Uninstall incomplete after {} of {} removals: {}".format(
                completed, len(removals), error
            ),
            file=sys.stderr,
        )
        return 1

    mode = "skills and configuration" if options.all else "skills only"
    print("Uninstalled dstack {}: {} removals completed.".format(mode, len(removals)))
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
