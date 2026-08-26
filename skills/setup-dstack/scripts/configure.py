#!/usr/bin/env python3
"""Read, validate, and atomically update dstack configuration."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


SCHEMA_VERSION = 2
PROFILES = ("fast-explorer", "feature-worker", "bug-worker", "skeptical-reviewer")
HOST_PATTERN = re.compile(r"^(?:auto|[a-z][a-z0-9-]*)$")


class ConfigError(Exception):
    pass


def default_config() -> Dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "host_override": "auto", "hosts": {}}


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


def validate_host(value: Any, location: str, allow_auto: bool = False) -> str:
    host = require_identifier(value, location)
    if not HOST_PATTERN.fullmatch(host) or (host == "auto" and not allow_auto):
        expected = "auto or a lowercase host id" if allow_auto else "a lowercase host id"
        raise ConfigError("{} must be {}".format(location, expected))
    return host


def validate_binding(value: Any, location: str) -> Dict[str, str]:
    binding = require_object(value, location)
    require_exact_keys(binding, ("model", "effort"), (), location)
    checked = {
        "model": require_identifier(binding["model"], "{}.model".format(location)),
        "effort": require_identifier(binding["effort"], "{}.effort".format(location)),
    }
    if checked["model"] == "inherit-parent" and checked["effort"] != "inherit-parent":
        raise ConfigError("{}.effort must be inherit-parent when model is inherit-parent".format(location))
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


def validate_transcripts_directory(value: Any, location: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value or not Path(value).expanduser().is_absolute():
        raise ConfigError("{} must be an absolute path or null".format(location))
    return str(Path(value).expanduser())


def validate_config(value: Any) -> Dict[str, Any]:
    config = require_object(value, "config")
    require_exact_keys(config, ("schema_version", "host_override", "hosts"), (), "config")
    if config["schema_version"] != SCHEMA_VERSION or isinstance(config["schema_version"], bool):
        raise ConfigError("config.schema_version must be {}; found {}".format(SCHEMA_VERSION, config["schema_version"]))
    hosts = require_object(config["hosts"], "config.hosts")
    checked_hosts: Dict[str, Any] = {}
    for host in sorted(hosts):
        validate_host(host, "config host key")
        location = "config.hosts.{}".format(host)
        entry = require_object(hosts[host], location)
        require_exact_keys(entry, ("profiles", "invalid_bindings", "transcripts_directory"), (), location)
        checked_hosts[host] = {
            "profiles": validate_profiles(entry["profiles"], "{}.profiles".format(location)),
            "invalid_bindings": validate_invalid_bindings(entry["invalid_bindings"], "{}.invalid_bindings".format(location)),
            "transcripts_directory": validate_transcripts_directory(entry["transcripts_directory"], "{}.transcripts_directory".format(location)),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "host_override": validate_host(config["host_override"], "config.host_override", allow_auto=True),
        "hosts": checked_hosts,
    }


def validate_proposal(value: Any) -> Dict[str, Any]:
    proposal = require_object(value, "proposal")
    require_exact_keys(
        proposal,
        ("host", "profiles", "invalid_bindings", "transcripts_directory"),
        ("host_override",),
        "proposal",
    )
    checked = {
        "host": validate_host(proposal["host"], "proposal.host"),
        "profiles": validate_profiles(proposal["profiles"], "proposal.profiles"),
        "invalid_bindings": validate_invalid_bindings(proposal["invalid_bindings"], "proposal.invalid_bindings"),
        "transcripts_directory": validate_transcripts_directory(proposal["transcripts_directory"], "proposal.transcripts_directory"),
    }
    if "host_override" in proposal:
        checked["host_override"] = validate_host(proposal["host_override"], "proposal.host_override", allow_auto=True)
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
    merged["hosts"][proposal["host"]] = {
        "profiles": copy.deepcopy(proposal["profiles"]),
        "invalid_bindings": copy.deepcopy(proposal["invalid_bindings"]),
        "transcripts_directory": proposal["transcripts_directory"],
    }
    if "host_override" in proposal:
        merged["host_override"] = proposal["host_override"]
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


def config_path(value: Optional[str]) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return (Path(os.environ.get("DSTACK_HOME", "~/.dstack")).expanduser() / "config.json").resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Manage dstack configuration.")
    result.add_argument("--config", metavar="PATH")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("validate")
    apply = commands.add_parser("apply")
    apply.add_argument("--proposal", required=True, metavar="PATH|-")
    return result


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    path = config_path(options.config)
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
        print("Configured host {} in {}".format(proposal["host"], path))
        return 0
    except (ConfigError, OSError) as error:
        print("Configuration failed: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
