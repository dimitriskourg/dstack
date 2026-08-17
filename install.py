#!/usr/bin/env python3
"""Install dstack without overwriting existing skills or support files."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


SOURCE_ROOT = Path(__file__).resolve().parent
SUPPORT_DIRECTORIES = ("adapters", "contracts", "schemas", "runtime")
SUPPORT_FILES = ("LICENSE", "NOTICE.md")


def path_exists(path: Path) -> bool:
    """Return true for files, directories, valid links, and broken links."""

    return os.path.lexists(str(path))


@dataclass(frozen=True)
class Operation:
    kind: str
    source: Path
    destination: Path

    def preview(self) -> str:
        verb = "link" if self.kind == "link" else "copy"
        return "Would {}: {} -> {}".format(verb, self.source, self.destination)

    def completed(self) -> str:
        verb = "Linked" if self.kind == "link" else "Copied"
        return "{}: {} -> {}".format(verb, self.source, self.destination)


class InstallError(Exception):
    pass


def skill_directories(source_root: Path) -> List[Path]:
    skills_root = source_root / "skills"
    if not skills_root.is_dir():
        raise InstallError("source skills directory is missing: {}".format(skills_root))

    skills = sorted(
        path
        for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    if not skills:
        raise InstallError("no skill packages found under {}".format(skills_root))
    return skills


def build_operations(
    source_root: Path,
    skills_directory: Path,
    dstack_home: Path,
    claude_skills_directory: Path,
    with_claude_links: bool,
) -> List[Operation]:
    skills = skill_directories(source_root)
    operations = [
        Operation("copy-directory", skill, skills_directory / skill.name)
        for skill in skills
    ]

    for name in SUPPORT_DIRECTORIES:
        source = source_root / name
        if source.is_dir():
            operations.append(Operation("copy-directory", source, dstack_home / name))

    for name in SUPPORT_FILES:
        source = source_root / name
        if not source.is_file():
            raise InstallError("required support file is missing: {}".format(source))
        operations.append(Operation("copy-file", source, dstack_home / name))

    if with_claude_links:
        operations.extend(
            Operation(
                "link",
                skills_directory / skill.name,
                claude_skills_directory / skill.name,
            )
            for skill in skills
        )

    return operations


def collision_paths(operations: Iterable[Operation]) -> List[Path]:
    return sorted(
        (operation.destination for operation in operations if path_exists(operation.destination)),
        key=str,
    )


def remove_created(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(str(path))


def apply_operations(operations: Sequence[Operation]) -> None:
    created: List[Path] = []
    try:
        for operation in operations:
            operation.destination.parent.mkdir(parents=True, exist_ok=True)
            if operation.kind == "copy-directory":
                shutil.copytree(str(operation.source), str(operation.destination))
            elif operation.kind == "copy-file":
                shutil.copy2(str(operation.source), str(operation.destination))
            elif operation.kind == "link":
                operation.destination.symlink_to(operation.source, target_is_directory=True)
            else:
                raise InstallError("unknown operation kind: {}".format(operation.kind))
            created.append(operation.destination)
    except Exception:
        for path in reversed(created):
            remove_created(path)
        raise


def resolve_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def parser() -> argparse.ArgumentParser:
    default_dstack_home = os.environ.get("DSTACK_HOME", "~/.dstack")
    result = argparse.ArgumentParser(
        description="Install dstack without overwriting existing files."
    )
    result.add_argument(
        "--dry-run",
        action="store_true",
        help="show the complete installation plan without changing files",
    )
    result.add_argument(
        "--with-claude-links",
        action="store_true",
        help="create one compatibility link per skill under the Claude skills directory",
    )
    result.add_argument(
        "--skills-dir",
        default="~/.agents/skills",
        metavar="PATH",
        help="canonical skill destination (default: ~/.agents/skills)",
    )
    result.add_argument(
        "--dstack-home",
        default=default_dstack_home,
        metavar="PATH",
        help="support-file destination (default: DSTACK_HOME or ~/.dstack)",
    )
    result.add_argument(
        "--claude-skills-dir",
        default="~/.claude/skills",
        metavar="PATH",
        help="Claude compatibility-link destination (default: ~/.claude/skills)",
    )
    return result


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    try:
        operations = build_operations(
            source_root=SOURCE_ROOT,
            skills_directory=resolve_path(options.skills_dir),
            dstack_home=resolve_path(options.dstack_home),
            claude_skills_directory=resolve_path(options.claude_skills_dir),
            with_claude_links=options.with_claude_links,
        )
        collisions = collision_paths(operations)
        if options.dry_run:
            for operation in operations:
                print(operation.preview())
            if collisions:
                print("Dry run found destination collisions:", file=sys.stderr)
                for path in collisions:
                    print("- {}".format(path), file=sys.stderr)
                print(
                    "Dry run complete: {} operations previewed; no files changed; "
                    "a real installation would stop.".format(len(operations)),
                    file=sys.stderr,
                )
                return 2
            print("Dry run complete: {} operations; no files changed.".format(len(operations)))
            return 0

        if collisions:
            print("Installation stopped; these destinations already exist:", file=sys.stderr)
            for path in collisions:
                print("- {}".format(path), file=sys.stderr)
            print("No files changed.", file=sys.stderr)
            return 2

        apply_operations(operations)
        for operation in operations:
            print(operation.completed())
        print("Installed dstack: {} operations completed.".format(len(operations)))
        return 0
    except (InstallError, OSError) as error:
        print("Installation failed: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
