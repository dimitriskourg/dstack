#!/usr/bin/env python3
"""Read, validate, and atomically update dstack model configuration."""

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


SCHEMA_VERSION = 1
ROLES = (
    "fast-explorer",
    "feature-worker",
    "bug-worker",
    "deep-judgment",
    "skeptical-reviewer",
    "independent-judge",
)
DEFAULT_PANELS = {
    "arena-runners": ["skeptical-reviewer", "deep-judgment"],
    "arena-cross-judge": ["independent-judge"],
    "interrogate-reviewers": [
        "deep-judgment",
        "bug-worker",
        "fast-explorer",
        "skeptical-reviewer",
    ],
    "architect-runners": ["deep-judgment", "skeptical-reviewer"],
}
HOST_PATTERN = re.compile(r"^(?:auto|[a-z][a-z0-9-]*)$")


class ConfigError(Exception):
    pass


def default_config() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "host_override": "auto",
        "hosts": {},
        "panels": copy.deepcopy(DEFAULT_PANELS),
    }


def require_object(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError("{} must be an object".format(location))
    return value


def require_exact_keys(
    value: Mapping[str, Any], required: Sequence[str], optional: Sequence[str], location: str
) -> None:
    keys = set(value)
    missing = set(required) - keys
    unknown = keys - set(required) - set(optional)
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


def validate_roles(value: Any, location: str) -> Dict[str, str]:
    roles = require_object(value, location)
    require_exact_keys(roles, ROLES, (), location)
    return {
        role: require_identifier(roles[role], "{}.{}".format(location, role))
        for role in ROLES
    }


def validate_stale_models(value: Any, location: str) -> List[str]:
    if not isinstance(value, list):
        raise ConfigError("{} must be an array".format(location))
    models = [
        require_identifier(model, "{}[{}]".format(location, index))
        for index, model in enumerate(value)
    ]
    if len(models) != len(set(models)):
        raise ConfigError("{} must not contain duplicates".format(location))
    return models


def validate_panels(value: Any, location: str = "panels") -> Dict[str, List[str]]:
    panels = require_object(value, location)
    require_exact_keys(panels, tuple(DEFAULT_PANELS), (), location)
    result: Dict[str, List[str]] = {}
    for name in DEFAULT_PANELS:
        members = panels[name]
        if not isinstance(members, list) or not members:
            raise ConfigError("{}.{} must be a non-empty array".format(location, name))
        checked: List[str] = []
        for index, member in enumerate(members):
            role = require_identifier(
                member, "{}.{}[{}]".format(location, name, index)
            )
            if role not in ROLES:
                raise ConfigError(
                    "{}.{}[{}] is not a semantic role: {}".format(
                        location, name, index, role
                    )
                )
            checked.append(role)
        result[name] = checked
    return result


def validate_config(value: Any) -> Dict[str, Any]:
    config = require_object(value, "config")
    require_exact_keys(
        config,
        ("schema_version", "host_override", "hosts", "panels"),
        (),
        "config",
    )
    if (
        not isinstance(config["schema_version"], int)
        or isinstance(config["schema_version"], bool)
        or config["schema_version"] != SCHEMA_VERSION
    ):
        raise ConfigError(
            "config.schema_version must be {}; found {}".format(
                SCHEMA_VERSION, config["schema_version"]
            )
        )
    host_override = validate_host(
        config["host_override"], "config.host_override", allow_auto=True
    )
    hosts = require_object(config["hosts"], "config.hosts")
    checked_hosts: Dict[str, Any] = {}
    for host in sorted(hosts):
        validate_host(host, "config host key")
        entry = require_object(hosts[host], "config.hosts.{}".format(host))
        require_exact_keys(
            entry,
            ("roles", "stale_models"),
            (),
            "config.hosts.{}".format(host),
        )
        checked_hosts[host] = {
            "roles": validate_roles(
                entry["roles"], "config.hosts.{}.roles".format(host)
            ),
            "stale_models": validate_stale_models(
                entry["stale_models"],
                "config.hosts.{}.stale_models".format(host),
            ),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "host_override": host_override,
        "hosts": checked_hosts,
        "panels": validate_panels(config["panels"]),
    }


def validate_proposal(value: Any) -> Dict[str, Any]:
    proposal = require_object(value, "proposal")
    require_exact_keys(
        proposal,
        ("host", "roles", "stale_models"),
        ("host_override", "panels"),
        "proposal",
    )
    checked = {
        "host": validate_host(proposal["host"], "proposal.host"),
        "roles": validate_roles(proposal["roles"], "proposal.roles"),
        "stale_models": validate_stale_models(
            proposal["stale_models"], "proposal.stale_models"
        ),
    }
    if "host_override" in proposal:
        checked["host_override"] = validate_host(
            proposal["host_override"], "proposal.host_override", allow_auto=True
        )
    if "panels" in proposal:
        checked["panels"] = validate_panels(proposal["panels"], "proposal.panels")
    return checked


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(
            "{} is not valid JSON at line {}, column {}: {}".format(
                label, error.lineno, error.colno, error.msg
            )
        ) from error
    except OSError as error:
        raise ConfigError("cannot read {}: {}".format(label, error)) from error


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return default_config()
    return validate_config(read_json(path, str(path)))


def load_proposal(path: str) -> Dict[str, Any]:
    if path == "-":
        try:
            return validate_proposal(json.load(sys.stdin))
        except json.JSONDecodeError as error:
            raise ConfigError(
                "stdin is not valid JSON at line {}, column {}: {}".format(
                    error.lineno, error.colno, error.msg
                )
            ) from error
    return validate_proposal(read_json(Path(path), "proposal {}".format(path)))


def merge_proposal(config: Mapping[str, Any], proposal: Mapping[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(config)
    host = proposal["host"]
    merged["hosts"][host] = {
        "roles": copy.deepcopy(proposal["roles"]),
        "stale_models": list(proposal["stale_models"]),
    }
    if "host_override" in proposal:
        merged["host_override"] = proposal["host_override"]
    if "panels" in proposal:
        merged["panels"] = copy.deepcopy(proposal["panels"])
    return validate_config(merged)


def write_atomic(path: Path, config: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=".config.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
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
    root = Path(os.environ.get("DSTACK_HOME", "~/.dstack")).expanduser()
    return (root / "config.json").resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Manage dstack model configuration.")
    result.add_argument(
        "--config",
        metavar="PATH",
        help="configuration path (default: DSTACK_HOME/config.json)",
    )
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("show", help="print the validated config or implicit defaults")
    commands.add_parser("validate", help="validate the config or implicit defaults")
    apply = commands.add_parser("apply", help="atomically apply one confirmed host proposal")
    apply.add_argument(
        "--proposal",
        required=True,
        metavar="PATH|-",
        help="proposal JSON file, or - to read JSON from stdin",
    )
    return result


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    path = config_path(options.config)
    try:
        config = load_config(path)
        if options.command == "show":
            print(json.dumps(config, indent=2, ensure_ascii=False))
            return 0
        if options.command == "validate":
            state = "file" if path.exists() else "implicit defaults"
            print("Valid dstack configuration ({}): {}".format(state, path))
            return 0
        proposal = load_proposal(options.proposal)
        merged = merge_proposal(config, proposal)
        write_atomic(path, merged)
        print("Configured host {} in {}".format(proposal["host"], path))
        return 0
    except (ConfigError, OSError) as error:
        print("Configuration failed: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
