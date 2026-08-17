#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "setup-dstack"
    / "scripts"
    / "configure.py"
)
SPEC = importlib.util.spec_from_file_location("dstack_configure", SCRIPT)
assert SPEC and SPEC.loader
CONFIGURE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONFIGURE
SPEC.loader.exec_module(CONFIGURE)


class ConfiguratorTests(unittest.TestCase):
    def roles(self, prefix: str):
        return {role: "{}-{}".format(prefix, role) for role in CONFIGURE.ROLES}

    def proposal(self, host: str, prefix: str):
        return {
            "host": host,
            "roles": self.roles(prefix),
            "stale_models": [],
        }

    def write_json(self, path: Path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def run_configurator(self, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = CONFIGURE.run(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def apply(self, config: Path, proposal: Path):
        return self.run_configurator(
            ["--config", str(config), "apply", "--proposal", str(proposal)]
        )

    def test_show_uses_implicit_defaults_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"

            status, stdout, stderr = self.run_configurator(
                ["--config", str(config), "show"]
            )

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertEqual(CONFIGURE.default_config(), json.loads(stdout))
            self.assertFalse(config.exists())

    def test_codex_and_cursor_settings_coexist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            codex = root / "codex.json"
            cursor = root / "cursor.json"
            self.write_json(codex, self.proposal("codex", "codex-model"))
            self.write_json(cursor, self.proposal("cursor", "cursor-model"))

            first_status, _, first_error = self.apply(config, codex)
            second_status, _, second_error = self.apply(config, cursor)

            self.assertEqual(0, first_status)
            self.assertEqual(0, second_status)
            self.assertEqual("", first_error + second_error)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.roles("codex-model"), saved["hosts"]["codex"]["roles"])
            self.assertEqual(self.roles("cursor-model"), saved["hosts"]["cursor"]["roles"])
            self.assertEqual(CONFIGURE.DEFAULT_PANELS, saved["panels"])

    def test_updating_one_host_and_panels_preserves_the_other_host(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            first = root / "first.json"
            second = root / "second.json"
            update = root / "update.json"
            self.write_json(first, self.proposal("codex", "codex-old"))
            self.write_json(second, self.proposal("cursor", "cursor-stays"))
            self.apply(config, first)
            self.apply(config, second)
            changed = self.proposal("codex", "codex-new")
            changed["panels"] = {
                **CONFIGURE.DEFAULT_PANELS,
                "arena-runners": ["independent-judge", "skeptical-reviewer"],
            }
            changed["host_override"] = "codex"
            self.write_json(update, changed)

            status, _, stderr = self.apply(config, update)

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.roles("codex-new"), saved["hosts"]["codex"]["roles"])
            self.assertEqual(self.roles("cursor-stays"), saved["hosts"]["cursor"]["roles"])
            self.assertEqual("codex", saved["host_override"])
            self.assertEqual(
                ["independent-judge", "skeptical-reviewer"],
                saved["panels"]["arena-runners"],
            )

    def test_invalid_proposal_leaves_existing_config_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            good = root / "good.json"
            bad = root / "bad.json"
            self.write_json(good, self.proposal("codex", "stable"))
            self.apply(config, good)
            original = config.read_bytes()
            invalid = self.proposal("cursor", "candidate")
            del invalid["roles"]["bug-worker"]
            self.write_json(bad, invalid)

            status, _, stderr = self.apply(config, bad)

            self.assertEqual(2, status)
            self.assertIn("proposal.roles is missing: bug-worker", stderr)
            self.assertEqual(original, config.read_bytes())

    def test_unsupported_existing_schema_version_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            existing = CONFIGURE.default_config()
            existing["schema_version"] = 2
            config.write_text(json.dumps(existing), encoding="utf-8")
            original = config.read_bytes()
            self.write_json(proposal, self.proposal("codex", "candidate"))

            status, _, stderr = self.apply(config, proposal)

            self.assertEqual(2, status)
            self.assertIn("config.schema_version must be 1; found 2", stderr)
            self.assertEqual(original, config.read_bytes())

    def test_replace_failure_preserves_previous_file_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            original = CONFIGURE.default_config()
            config.write_text(json.dumps(original), encoding="utf-8")
            changed = CONFIGURE.default_config()
            changed["host_override"] = "codex"

            with mock.patch.object(CONFIGURE.os, "replace", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(OSError, "blocked"):
                    CONFIGURE.write_atomic(config, changed)

            self.assertEqual(original, json.loads(config.read_text(encoding="utf-8")))
            self.assertEqual([], list(root.glob(".config.*.tmp")))


if __name__ == "__main__":
    unittest.main()
