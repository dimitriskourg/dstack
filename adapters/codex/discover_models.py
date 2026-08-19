#!/usr/bin/env python3
"""Render the installed Codex model/effort catalog in a compact stable shape."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Mapping, Sequence


class CatalogError(Exception):
    pass


def run_codex(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("codex")
    if not executable:
        raise CatalogError("codex is not available on PATH")
    try:
        return subprocess.run(
            [executable] + list(arguments),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise CatalogError("cannot run codex: {}".format(error)) from error


def discover() -> Dict[str, List[str]]:
    help_result = run_codex(("debug", "--help"))
    help_text = "{}\n{}".format(help_result.stdout, help_result.stderr)
    if help_result.returncode != 0 or "models" not in help_text:
        raise CatalogError("the installed codex CLI does not advertise debug models")

    result = run_codex(("debug", "models"))
    if result.returncode != 0:
        detail = result.stderr.strip() or "exit status {}".format(result.returncode)
        raise CatalogError("codex debug models failed: {}".format(detail))
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CatalogError("codex debug models returned invalid JSON: {}".format(error)) from error
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise CatalogError("codex debug models returned an unsupported catalog shape")

    catalog: Dict[str, List[str]] = {}
    for index, raw_model in enumerate(payload["models"]):
        if not isinstance(raw_model, Mapping):
            raise CatalogError("catalog model {} must be an object".format(index))
        slug = raw_model.get("slug")
        levels = raw_model.get("supported_reasoning_levels")
        if not isinstance(slug, str) or not slug or any(char.isspace() for char in slug):
            raise CatalogError("catalog model {} has an invalid slug".format(index))
        if not isinstance(levels, list):
            raise CatalogError("catalog model {} has no reasoning-level list".format(slug))
        efforts: List[str] = []
        for level in levels:
            effort = level.get("effort") if isinstance(level, Mapping) else None
            if not isinstance(effort, str) or not effort or any(char.isspace() for char in effort):
                raise CatalogError("catalog model {} has an invalid effort".format(slug))
            if effort not in efforts:
                efforts.append(effort)
        if slug in catalog:
            raise CatalogError("catalog contains duplicate model slug: {}".format(slug))
        catalog[slug] = efforts
    return catalog


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Discover installed Codex models and efforts.")
    result.add_argument("--check", nargs=2, metavar=("MODEL", "EFFORT"))
    return result


def run(arguments: Sequence[str]) -> int:
    options = parser().parse_args(arguments)
    try:
        catalog = discover()
        if options.check:
            model, effort = options.check
            if model in catalog and effort in catalog[model]:
                print("valid")
                return 0
            print("invalid")
            return 2
        print(json.dumps({"host": "codex", "models": catalog}, indent=2))
        return 0
    except CatalogError as error:
        print("Codex model discovery unavailable: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
