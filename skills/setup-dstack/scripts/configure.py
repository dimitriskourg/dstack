#!/usr/bin/env python3
"""Read, validate, and atomically update dstack configuration."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


SCHEMA_VERSION = 2
CONFIG_PATH = Path("~/.dstack/config.json").expanduser()
CONFIG_DISPLAY = "~/.dstack/config.json"
PROFILES = ("fast-explorer", "feature-worker", "bug-worker", "skeptical-reviewer")
RESERVED_BINDING_VALUES = {"auto", "inherit", "inherit-parent"}
PROFILE_FIELDS = {"codex": ("model", "effort"), "claude": ("model", "effort"), "cursor": ("model",)}
SUPPORTED_HOSTS = tuple(PROFILE_FIELDS)
EFFORT_BRACKET = re.compile(r"^(?P<model>[^\[\]\s]+)\[effort=(?P<effort>[^\[\]\s,=]+)\]$")


class ConfigError(Exception):
    pass


def default_config() -> Dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "hosts": {}}


def require_object(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError("{} must be an object".format(location))
    return value


def require_exact_keys(
    value: Mapping[str, Any], required: Sequence[str], optional: Sequence[str], location: str
) -> None:
    missing = set(required) - set(value)
    unknown = set(value) - set(required) - set(optional)
    if missing:
        raise ConfigError("{} is missing: {}".format(location, ", ".join(sorted(missing))))
    if unknown:
        raise ConfigError("{} has unknown keys: {}".format(location, ", ".join(sorted(unknown))))


def require_identifier(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise ConfigError("{} must be a non-empty string without whitespace".format(location))
    if any(char in "[]" for char in value):
        raise ConfigError("{} must not contain brackets".format(location))
    return value


def validate_host(value: Any, location: str) -> str:
    host = require_identifier(value, location)
    if host not in SUPPORTED_HOSTS:
        raise ConfigError("{} must be one of: {}".format(location, ", ".join(SUPPORTED_HOSTS)))
    return host


def require_concrete(value: str, location: str) -> str:
    if value in RESERVED_BINDING_VALUES:
        raise ConfigError(
            "{} must be a concrete value; auto, inherit, and inherit-parent are not supported".format(location)
        )
    return value


def validate_effort_carrying_model(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise ConfigError("{} must be a non-empty string without whitespace".format(location))
    if any(char in "[]" for char in value):
        match = EFFORT_BRACKET.fullmatch(value)
        if match is None:
            raise ConfigError("{} brackets must be exactly [effort=<value>]".format(location))
        require_concrete(match.group("model"), location)
        require_concrete(match.group("effort"), "{} effort".format(location))
        return value
    return require_concrete(value, location)


def validate_binding(host: str, value: Any, location: str) -> Dict[str, str]:
    binding = require_object(value, location)
    fields = PROFILE_FIELDS[host]
    require_exact_keys(binding, fields, (), location)
    if fields == ("model",):
        return {"model": validate_effort_carrying_model(binding["model"], "{}.model".format(location))}
    return {
        field: require_concrete(
            require_identifier(binding[field], "{}.{}".format(location, field)),
            "{}.{}".format(location, field),
        )
        for field in fields
    }


def validate_profiles(host: str, value: Any, location: str) -> Dict[str, Dict[str, str]]:
    profiles = require_object(value, location)
    require_exact_keys(profiles, PROFILES, (), location)
    return {
        profile: validate_binding(host, profiles[profile], "{}.{}".format(location, profile))
        for profile in PROFILES
    }


def validate_invalid_bindings(host: str, value: Any, location: str) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        raise ConfigError("{} must be an array".format(location))
    bindings = [
        validate_binding(host, item, "{}[{}]".format(location, index)) for index, item in enumerate(value)
    ]
    identities = [tuple(sorted(item.items())) for item in bindings]
    if len(identities) != len(set(identities)):
        raise ConfigError("{} must not contain duplicates".format(location))
    return bindings


def validate_transcripts_directory(value: Any, location: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value or not Path(value).expanduser().is_absolute():
        raise ConfigError("{} must be an absolute path or null".format(location))
    return str(Path(value).expanduser())


def validate_repository_root(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or not Path(value).expanduser().is_absolute():
        raise ConfigError("{} must be a canonical absolute path".format(location))
    resolved = str(Path(value).expanduser().resolve())
    if value != resolved:
        raise ConfigError("{} must be canonical; expected {}".format(location, resolved))
    return resolved


def validate_repositories(value: Any, location: str) -> Dict[str, Dict[str, Optional[str]]]:
    repositories = require_object(value, location)
    checked: Dict[str, Dict[str, Optional[str]]] = {}
    for key in sorted(repositories):
        repository_root = validate_repository_root(key, "{} key".format(location))
        entry_location = "{}[{}]".format(location, json.dumps(key))
        entry = require_object(repositories[key], entry_location)
        require_exact_keys(entry, ("repository_root", "transcripts_directory"), (), entry_location)
        recorded_root = validate_repository_root(
            entry["repository_root"], "{}.repository_root".format(entry_location)
        )
        if recorded_root != repository_root:
            raise ConfigError("{}.repository_root must match its repository key".format(entry_location))
        checked[repository_root] = {
            "repository_root": repository_root,
            "transcripts_directory": validate_transcripts_directory(
                entry["transcripts_directory"], "{}.transcripts_directory".format(entry_location)
            ),
        }
    return checked


def validate_config(value: Any) -> Dict[str, Any]:
    config = require_object(value, "config")
    require_exact_keys(config, ("schema_version", "hosts"), (), "config")
    if config["schema_version"] != SCHEMA_VERSION or isinstance(config["schema_version"], bool):
        raise ConfigError("config.schema_version must be {}; found {}".format(SCHEMA_VERSION, config["schema_version"]))
    hosts = require_object(config["hosts"], "config.hosts")
    checked_hosts: Dict[str, Any] = {}
    for host in sorted(hosts):
        validate_host(host, "config host key")
        location = "config.hosts.{}".format(host)
        entry = require_object(hosts[host], location)
        require_exact_keys(entry, ("profiles", "invalid_bindings", "repositories"), (), location)
        checked_hosts[host] = {
            "profiles": validate_profiles(host, entry["profiles"], "{}.profiles".format(location)),
            "invalid_bindings": validate_invalid_bindings(
                host, entry["invalid_bindings"], "{}.invalid_bindings".format(location)
            ),
            "repositories": validate_repositories(entry["repositories"], "{}.repositories".format(location)),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "hosts": checked_hosts,
    }


def validate_proposal(value: Any) -> Dict[str, Any]:
    proposal = require_object(value, "proposal")
    require_exact_keys(
        proposal,
        ("host", "repository_root", "profiles", "invalid_bindings", "transcripts_directory"),
        (),
        "proposal",
    )
    host = validate_host(proposal["host"], "proposal.host")
    checked = {
        "host": host,
        "repository_root": validate_repository_root(proposal["repository_root"], "proposal.repository_root"),
        "profiles": validate_profiles(host, proposal["profiles"], "proposal.profiles"),
        "invalid_bindings": validate_invalid_bindings(host, proposal["invalid_bindings"], "proposal.invalid_bindings"),
        "transcripts_directory": validate_transcripts_directory(proposal["transcripts_directory"], "proposal.transcripts_directory"),
    }
    return checked


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError("{} is not valid JSON at line {}, column {}: {}".format(label, error.lineno, error.colno, error.msg)) from error
    except OSError as error:
        raise ConfigError("cannot read {}: {}".format(label, error)) from error


def load_proposal(path: str) -> Dict[str, Any]:
    if path == "-":
        try:
            return validate_proposal(json.load(sys.stdin))
        except json.JSONDecodeError as error:
            raise ConfigError("stdin is not valid JSON: {}".format(error)) from error
    return validate_proposal(read_json(Path(path), "proposal {}".format(path)))


def git_text(arguments: Sequence[str], cwd: Optional[str] = None) -> str:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise ConfigError("cannot run git: {}".format(error)) from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ConfigError(detail)
    return completed.stdout.strip()


def canonicalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def current_checkout_root(checkout: Optional[str] = None) -> str:
    try:
        toplevel = git_text(["rev-parse", "--show-toplevel"], cwd=checkout)
    except ConfigError as error:
        raise ConfigError("no active Git repository: {}".format(error)) from error
    return canonicalize_path(toplevel)


def git_common_dir(checkout: str) -> str:
    raw = git_text(["rev-parse", "--git-common-dir"], cwd=checkout)
    path = Path(raw)
    if not path.is_absolute():
        path = Path(checkout) / path
    return str(path.resolve())


def worktree_roots(checkout: str) -> List[str]:
    porcelain = git_text(["worktree", "list", "--porcelain"], cwd=checkout)
    roots: List[str] = []
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            roots.append(canonicalize_path(line[len("worktree "):]))
    return roots


def select_repository_entry(
    config: Mapping[str, Any],
    host: str,
    checkout: Optional[str] = None,
) -> Dict[str, Any]:
    checked = validate_config(config)
    validate_host(host, "host")
    if host not in checked["hosts"]:
        raise ConfigError("host {!r} has no entry in {}".format(host, CONFIG_DISPLAY))
    checkout_root = current_checkout_root(checkout)
    repositories = checked["hosts"][host]["repositories"]
    if checkout_root in repositories:
        entry = repositories[checkout_root]
        return {
            "host": host,
            "checkout_root": checkout_root,
            "match": "exact",
            "repository_root": entry["repository_root"],
            "transcripts_directory": entry["transcripts_directory"],
        }

    checkout_common = git_common_dir(checkout_root)
    matches: List[Dict[str, Optional[str]]] = []
    for root, entry in repositories.items():
        if not Path(root).exists():
            continue
        try:
            registered_common = git_common_dir(root)
        except ConfigError:
            continue
        if registered_common == checkout_common:
            matches.append(entry)

    if not matches:
        if not repositories:
            raise ConfigError(
                "The canonical repository root is `{}`, but {} has no repository entries for host {}.".format(
                    checkout_root, CONFIG_DISPLAY, host
                )
            )
        registered = ", ".join("`{}`".format(root) for root in sorted(repositories))
        raise ConfigError(
            "The canonical repository root is `{}`, but {} only registers {}.".format(
                checkout_root, CONFIG_DISPLAY, registered
            )
        )

    by_root = {entry["repository_root"]: entry for entry in matches}
    selected = matches[0] if len(matches) == 1 else None
    if selected is None:
        for worktree in worktree_roots(checkout_root):
            if worktree in by_root:
                selected = by_root[worktree]
                break
        if selected is None:
            selected = sorted(matches, key=lambda entry: entry["repository_root"] or "")[0]

    return {
        "host": host,
        "checkout_root": checkout_root,
        "match": "linked-worktree",
        "repository_root": selected["repository_root"],
        "transcripts_directory": selected["transcripts_directory"],
    }


def merge_proposal(config: Mapping[str, Any], proposal: Mapping[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(config)
    previous = merged["hosts"].get(proposal["host"], {})
    repositories = copy.deepcopy(previous.get("repositories", {}))
    repositories[proposal["repository_root"]] = {
        "repository_root": proposal["repository_root"],
        "transcripts_directory": proposal["transcripts_directory"],
    }
    merged["hosts"][proposal["host"]] = {
        "profiles": copy.deepcopy(proposal["profiles"]),
        "invalid_bindings": copy.deepcopy(proposal["invalid_bindings"]),
        "repositories": repositories,
    }
    return validate_config(merged)


def write_atomic(path: Path, config: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(path.parent), prefix=".config.", suffix=".tmp", delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            json.dump(config, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    try:
        os.replace(str(temporary_path), str(path))
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Manage dstack configuration.")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("validate")
    apply = commands.add_parser("apply")
    apply.add_argument("--proposal", required=True, metavar="PATH|-")
    resolve = commands.add_parser("resolve")
    resolve.add_argument("--host", required=True)
    resolve.add_argument("--checkout")
    return result


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    path = CONFIG_PATH.resolve()
    try:
        if options.command in {"validate", "resolve"} and not path.exists():
            raise ConfigError("configuration file does not exist: {}".format(path))
        config = default_config() if not path.exists() else validate_config(read_json(path, str(path)))
        if options.command == "show":
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return 0
        if options.command == "validate":
            print("Valid dstack configuration: {}".format(path))
            return 0
        if options.command == "resolve":
            checkout = canonicalize_path(options.checkout) if options.checkout else None
            selected = select_repository_entry(config, options.host, checkout)
            print(json.dumps(selected, indent=2, ensure_ascii=False))
            return 0
        proposal = load_proposal(options.proposal)
        write_atomic(path, merge_proposal(config, proposal))
        print(
            "Configured host {} for repository {} in {}".format(
                proposal["host"], proposal["repository_root"], path
            )
        )
        return 0
    except (ConfigError, OSError) as error:
        print("Configuration failed: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
