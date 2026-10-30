#!/usr/bin/env python3
"""Install dstack or explicitly refresh a verified existing dstack copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # Windows-only; supplies CreateJunction.
    import _winapi
except ImportError:  # pragma: no cover - exercised on Windows only
    _winapi = None


SOURCE_ROOT = Path(__file__).resolve().parent
DSTACK_DIRECTORY = Path("~/.dstack").expanduser()
SUPPORT_DIRECTORIES = ("schemas",)
SUPPORT_FILES = ("LICENSE", "NOTICE.md")
# Records installed skills so --update can prune the ones the source dropped.
RECEIPT_NAME = "installed.json"
# stat exposes this only on Windows builds; the tag value itself is stable.
MOUNT_POINT_REPARSE_TAG = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)


def path_exists(path: Path) -> bool:
    """Return true for files, directories, valid links, and broken links."""

    return os.path.lexists(str(path))


def is_compatibility_link(path: Path) -> bool:
    """Return true for symlinks everywhere and for Windows directory junctions."""

    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        reparse_tag = os.lstat(str(path)).st_reparse_tag
    except (AttributeError, OSError):
        return False
    return reparse_tag == MOUNT_POINT_REPARSE_TAG


def create_compatibility_link(source: Path, destination: Path) -> None:
    """Link destination to source, preferring junctions on Windows.

    Real symlinks need Developer Mode or an elevated shell on Windows; a
    directory junction needs no special privilege and is discovered the same way.
    """

    if os.name == "nt":
        create_junction = getattr(_winapi, "CreateJunction", None)
        if create_junction is not None:
            create_junction(str(source), str(destination))
            return
    destination.symlink_to(source, target_is_directory=True)


@dataclass(frozen=True)
class Operation:
    kind: str
    source: Path
    destination: Path

    def preview(self) -> str:
        return "Would link" if self.kind == "link" else "Would copy"

    def completed(self) -> str:
        return "Linked" if self.kind == "link" else "Copied"


class InstallError(Exception):
    pass


def skill_identity(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.fullmatch(r"name:\s*['\"]?([a-z0-9-]+)['\"]?", line.strip())
        if match:
            return match.group(1)
    return ""


def tree_digest(root: Path) -> str:
    """Hash a skill tree, ignoring bytecode that running its scripts leaves behind."""

    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or not path.is_file():
            continue
        content = path.read_bytes()
        digest.update("{}\0{}\0".format(relative.as_posix(), len(content)).encode("utf-8"))
        digest.update(content)
    return digest.hexdigest()


def read_receipt(dstack_home: Path) -> Dict[str, str]:
    path = dstack_home / RECEIPT_NAME
    if not path_exists(path):
        return {}
    try:
        skills = json.loads(path.read_text(encoding="utf-8"))["skills"]
    except (ValueError, KeyError, TypeError) as error:
        raise InstallError(
            "install receipt is unreadable: {}: {}; delete it and rerun".format(path, error)
        )
    if not isinstance(skills, dict) or not all(
        isinstance(name, str) and isinstance(digest, str) for name, digest in skills.items()
    ):
        raise InstallError("install receipt is malformed: {}; delete it and rerun".format(path))
    return skills


def write_receipt(dstack_home: Path, skills: Dict[str, str]) -> None:
    dstack_home.mkdir(parents=True, exist_ok=True)
    path = dstack_home / RECEIPT_NAME
    staged = path.with_name(path.name + ".tmp")
    staged.write_text(
        json.dumps({"skills": dict(sorted(skills.items()))}, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(str(staged), str(path))


def plan_retirements(
    receipt: Dict[str, str],
    current_names: Iterable[str],
    skills_directory: Path,
    claude_skills_directory: Path,
) -> Tuple[List[Path], List[str], Dict[str, str]]:
    """Return removals, warnings, and the receipt entries still kept for retired skills."""

    current = set(current_names)
    removals: List[Path] = []
    warnings: List[str] = []
    kept: Dict[str, str] = {}
    for name, digest in sorted(receipt.items()):
        if name in current:
            continue
        skill = skills_directory / name
        link = claude_skills_directory / name
        if path_exists(skill):
            unchanged = (
                skill.is_dir()
                and not skill.is_symlink()
                and (skill / "SKILL.md").is_file()
                and skill_identity(skill / "SKILL.md") == name
                and tree_digest(skill) == digest
            )
            if not unchanged:
                warnings.append("kept retired skill that changed since install: {}".format(skill))
                kept[name] = digest
                continue
        if path_exists(link):
            if is_compatibility_link(link) and link.resolve() == skill.resolve():
                removals.append(link)
            else:
                warnings.append("kept Claude entry dstack does not own: {}".format(link))
        if path_exists(skill):
            removals.append(skill)
    return removals, warnings, kept


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


def update_issues(operations: Iterable[Operation]) -> List[str]:
    issues: List[str] = []
    for operation in operations:
        destination = operation.destination
        if not path_exists(destination):
            continue
        if operation.kind == "copy-directory":
            if not destination.is_dir() or destination.is_symlink():
                issues.append("expected installed directory: {}".format(destination))
                continue
            source_skill = operation.source / "SKILL.md"
            if source_skill.is_file():
                installed_skill = destination / "SKILL.md"
                if not installed_skill.is_file():
                    issues.append("installed skill has no SKILL.md: {}".format(destination))
                    continue
                if skill_identity(installed_skill) != operation.source.name:
                    issues.append("installed skill identity does not match: {}".format(destination))
        elif operation.kind == "copy-file":
            if not destination.is_file() or destination.is_symlink():
                issues.append("expected installed file: {}".format(destination))
        elif operation.kind == "link":
            if not is_compatibility_link(destination):
                issues.append("expected compatibility link: {}".format(destination))
            elif destination.resolve() != operation.source.resolve():
                issues.append("compatibility link points elsewhere: {}".format(destination))
        else:
            issues.append("updates do not manage operation kind {}: {}".format(operation.kind, destination))
    return issues


def remove_created(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif is_compatibility_link(path):
        # A junction reports as a directory; rmdir drops the link, rmtree would
        # delete the skills it points at.
        os.rmdir(str(path))
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
                create_compatibility_link(operation.source, operation.destination)
            else:
                raise InstallError("unknown operation kind: {}".format(operation.kind))
            created.append(operation.destination)
    except Exception:
        for path in reversed(created):
            remove_created(path)
        raise


def stage_update(operation: Operation) -> Path:
    operation.destination.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(
        tempfile.mkdtemp(
            prefix=".dstack-update-{}-".format(operation.destination.name),
            dir=str(operation.destination.parent),
        )
    )
    staged = stage_root / "staged"
    try:
        if operation.kind == "copy-directory":
            shutil.copytree(str(operation.source), str(staged))
        elif operation.kind == "copy-file":
            shutil.copy2(str(operation.source), str(staged))
        else:
            raise InstallError("updates do not support operation kind: {}".format(operation.kind))
    except Exception:
        shutil.rmtree(str(stage_root), ignore_errors=True)
        raise
    return stage_root


def apply_updates(operations: Sequence[Operation]) -> List[Tuple[Operation, str]]:
    staged: List[Tuple[Operation, Optional[Path]]] = []
    try:
        for operation in operations:
            staged.append(
                (operation, None if operation.kind == "link" else stage_update(operation))
            )
    except Exception:
        for _, stage_root in staged:
            if stage_root is not None:
                shutil.rmtree(str(stage_root), ignore_errors=True)
        raise
    replaced = []
    outcomes: List[Tuple[Operation, str]] = []
    try:
        for operation, stage_root in staged:
            if operation.kind == "link":
                if path_exists(operation.destination):
                    outcomes.append((operation, "Already linked"))
                    continue
                operation.destination.parent.mkdir(parents=True, exist_ok=True)
                create_compatibility_link(operation.source, operation.destination)
                replaced.append((operation.destination, None))
                outcomes.append((operation, "Linked"))
                continue
            backup = stage_root / "backup"
            had_destination = path_exists(operation.destination)
            if had_destination:
                operation.destination.rename(backup)
            try:
                (stage_root / "staged").rename(operation.destination)
            except Exception:
                if had_destination:
                    backup.rename(operation.destination)
                raise
            replaced.append((operation.destination, backup if had_destination else None))
            outcomes.append((operation, "Updated"))
    except Exception:
        for destination, backup in reversed(replaced):
            remove_created(destination)
            if backup is not None:
                backup.rename(destination)
        raise
    finally:
        for _, stage_root in staged:
            if stage_root is not None:
                shutil.rmtree(str(stage_root), ignore_errors=True)
    return outcomes


def print_outcomes(outcomes: Iterable[Tuple[Operation, str]], verbose: bool) -> None:
    """Print each outcome when verbose, else one count per verb and destination directory."""

    if verbose:
        for operation, verb in outcomes:
            print("{}: {} -> {}".format(verb, operation.source, operation.destination))
        return
    counts: Dict[Tuple[str, Path], int] = {}
    for operation, verb in outcomes:
        key = (verb, operation.destination.parent)
        counts[key] = counts.get(key, 0) + 1
    for (verb, directory), count in counts.items():
        print("{}: {} in {}".format(verb, count, directory))


def resolve_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Install dstack without overwriting existing files."
    )
    result.add_argument(
        "--dry-run",
        action="store_true",
        help="show the complete installation plan without changing files",
    )
    result.add_argument(
        "--verbose",
        action="store_true",
        help="list every path instead of a count per destination directory",
    )
    result.add_argument(
        "--update",
        action="store_true",
        help="sync verified existing and missing dstack artifacts while preserving config.json",
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
            dstack_home=DSTACK_DIRECTORY.resolve(),
            claude_skills_directory=resolve_path(options.claude_skills_dir),
            with_claude_links=options.with_claude_links,
        )
        dstack_home = DSTACK_DIRECTORY.resolve()
        skills = skill_directories(SOURCE_ROOT)
        receipt = read_receipt(dstack_home)
        installed = {skill.name: tree_digest(skill) for skill in skills}
        if options.update:
            retired, retirement_warnings, kept = plan_retirements(
                receipt,
                installed,
                resolve_path(options.skills_dir),
                resolve_path(options.claude_skills_dir),
            )
            update_roots = (
                resolve_path(options.skills_dir),
                DSTACK_DIRECTORY.resolve(),
            )
            issues = [
                "expected existing update root: {}".format(root)
                for root in update_roots
                if not root.is_dir() or root.is_symlink()
            ] + update_issues(operations)
            if options.dry_run:
                print_outcomes(
                    (
                        (operation, "Would link" if operation.kind == "link" else "Would update")
                        for operation in operations
                    ),
                    options.verbose,
                )
                for path in retired:
                    print("Would remove retired: {}".format(path))
                for warning in retirement_warnings:
                    print("Warning: {}".format(warning), file=sys.stderr)
                if issues:
                    print("Update dry run found ownership or topology problems:", file=sys.stderr)
                    for issue in issues:
                        print("- {}".format(issue), file=sys.stderr)
                    print("No files changed.", file=sys.stderr)
                    return 2
                print("Update dry run complete: {} operations; no files changed.".format(len(operations)))
                return 0
            if issues:
                print("Update stopped before writes:", file=sys.stderr)
                for issue in issues:
                    print("- {}".format(issue), file=sys.stderr)
                print("No files changed.", file=sys.stderr)
                return 2
            print_outcomes(apply_updates(operations), options.verbose)
            for path in retired:
                remove_created(path)
                print("Removed retired: {}".format(path))
            for warning in retirement_warnings:
                print("Warning: {}".format(warning), file=sys.stderr)
            write_receipt(dstack_home, {**kept, **installed})
            print(
                "Updated dstack: {} operations completed; config.json was preserved.".format(
                    len(operations)
                )
            )
            return 0
        collisions = collision_paths(operations)
        if options.dry_run:
            print_outcomes(
                ((operation, operation.preview()) for operation in operations), options.verbose
            )
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
        write_receipt(dstack_home, {**receipt, **installed})
        print_outcomes(
            ((operation, operation.completed()) for operation in operations), options.verbose
        )
        print("Installed dstack: {} operations completed.".format(len(operations)))
        return 0
    except (InstallError, OSError) as error:
        print("Installation failed: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
