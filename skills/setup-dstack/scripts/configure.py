#!/usr/bin/env python3
"""Read, validate, and atomically update dstack configuration."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


SCHEMA_VERSION = 2
CONFIG_PATH = Path("~/.dstack/config.json").expanduser()
PROFILES = ("fast-explorer", "feature-worker", "bug-worker", "skeptical-reviewer")
RESERVED_BINDING_VALUES = {"auto", "inherit-parent"}
SPAWN_ARGUMENTS = "spawn-arguments"
WORKER_DEFINITIONS = "worker-definitions"
WORKER_MECHANISMS = (SPAWN_ARGUMENTS, WORKER_DEFINITIONS)
SUPPORTED_HOSTS = ("codex", "claude", "cursor")


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
    return value


def validate_host(value: Any, location: str) -> str:
    host = require_identifier(value, location)
    if host not in SUPPORTED_HOSTS:
        raise ConfigError("{} must be one of: {}".format(location, ", ".join(SUPPORTED_HOSTS)))
    return host


def validate_binding(value: Any, location: str) -> Dict[str, str]:
    binding = require_object(value, location)
    require_exact_keys(binding, ("model", "effort"), (), location)
    checked: Dict[str, str] = {
        "model": require_identifier(binding["model"], "{}.model".format(location)),
        "effort": require_identifier(binding["effort"], "{}.effort".format(location)),
    }
    for field in ("model", "effort"):
        if checked[field] in RESERVED_BINDING_VALUES:
            raise ConfigError(
                "{}.{} must be a concrete value; auto and inherit-parent are not supported".format(
                    location, field
                )
            )
    return checked


def validate_profiles(value: Any, location: str) -> Dict[str, Dict[str, str]]:
    profiles = require_object(value, location)
    require_exact_keys(profiles, PROFILES, (), location)
    return {
        profile: validate_binding(profiles[profile], "{}.{}".format(location, profile))
        for profile in PROFILES
    }


def validate_invalid_bindings(value: Any, location: str) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        raise ConfigError("{} must be an array".format(location))
    bindings = [validate_binding(item, "{}[{}]".format(location, index)) for index, item in enumerate(value)]
    identities = [(item["model"], item["effort"]) for item in bindings]
    if len(identities) != len(set(identities)):
        raise ConfigError("{} must not contain duplicates".format(location))
    return bindings


def validate_worker_binding(value: Any, location: str) -> Dict[str, Any]:
    binding = require_object(value, location)
    require_exact_keys(binding, ("mechanism", "definitions_directory"), (), location)
    mechanism = require_identifier(binding["mechanism"], "{}.mechanism".format(location))
    if mechanism not in WORKER_MECHANISMS:
        raise ConfigError(
            "{}.mechanism must be one of: {}".format(location, ", ".join(WORKER_MECHANISMS))
        )
    directory = binding["definitions_directory"]
    if mechanism == WORKER_DEFINITIONS:
        if not isinstance(directory, str) or not directory or not Path(directory).expanduser().is_absolute():
            raise ConfigError(
                "{}.definitions_directory must be an absolute path when the mechanism is {}".format(
                    location, WORKER_DEFINITIONS
                )
            )
        return {"mechanism": mechanism, "definitions_directory": str(Path(directory).expanduser())}
    if directory is not None:
        raise ConfigError(
            "{}.definitions_directory must be null when the mechanism is {}".format(location, SPAWN_ARGUMENTS)
        )
    return {"mechanism": mechanism, "definitions_directory": None}


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
        require_exact_keys(entry, ("profiles", "invalid_bindings", "worker_binding", "repositories"), (), location)
        checked_hosts[host] = {
            "profiles": validate_profiles(entry["profiles"], "{}.profiles".format(location)),
            "invalid_bindings": validate_invalid_bindings(entry["invalid_bindings"], "{}.invalid_bindings".format(location)),
            "worker_binding": validate_worker_binding(entry["worker_binding"], "{}.worker_binding".format(location)),
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
        ("host", "repository_root", "profiles", "invalid_bindings", "worker_binding", "transcripts_directory"),
        (),
        "proposal",
    )
    checked = {
        "host": validate_host(proposal["host"], "proposal.host"),
        "repository_root": validate_repository_root(proposal["repository_root"], "proposal.repository_root"),
        "profiles": validate_profiles(proposal["profiles"], "proposal.profiles"),
        "invalid_bindings": validate_invalid_bindings(proposal["invalid_bindings"], "proposal.invalid_bindings"),
        "worker_binding": validate_worker_binding(proposal["worker_binding"], "proposal.worker_binding"),
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
        "worker_binding": copy.deepcopy(proposal["worker_binding"]),
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
    return result


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    path = CONFIG_PATH.resolve()
    try:
        config = default_config() if not path.exists() else validate_config(read_json(path, str(path)))
        if options.command == "show":
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return 0
        if options.command == "validate":
            state = "file" if path.exists() else "implicit defaults"
            print("Valid dstack configuration ({}): {}".format(state, path))
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
