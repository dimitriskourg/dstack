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


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "setup-dstack" / "scripts" / "configure.py"
SPEC = importlib.util.spec_from_file_location("dstack_configure", SCRIPT)
assert SPEC and SPEC.loader
CONFIGURE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONFIGURE
SPEC.loader.exec_module(CONFIGURE)


class ConfiguratorTests(unittest.TestCase):
    def profiles(self, prefix: str):
        return {
            profile: {"model": "{}-{}".format(prefix, profile), "effort": "medium"}
            for profile in CONFIGURE.PROFILES
        }

    def proposal(self, host: str, prefix: str, transcripts: str = "/tmp/transcripts"):
        return {
            "host": host,
            "profiles": self.profiles(prefix),
            "invalid_bindings": [],
            "transcripts_directory": transcripts,
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
        return self.run_configurator(["--config", str(config), "apply", "--proposal", str(proposal)])

    def test_show_uses_implicit_defaults_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            status, stdout, stderr = self.run_configurator(["--config", str(config), "show"])
            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertEqual(CONFIGURE.default_config(), json.loads(stdout))
            self.assertFalse(config.exists())

    def test_host_settings_and_transcript_paths_coexist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            first = root / "first.json"
            second = root / "second.json"
            self.write_json(first, self.proposal("host-a", "alpha", "/tmp/a-transcripts"))
            self.write_json(second, self.proposal("host-b", "beta", "/tmp/b-transcripts"))
            self.assertEqual(0, self.apply(config, first)[0])
            self.assertEqual(0, self.apply(config, second)[0])
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.profiles("alpha"), saved["hosts"]["host-a"]["profiles"])
            self.assertEqual("/tmp/b-transcripts", saved["hosts"]["host-b"]["transcripts_directory"])

    def test_update_preserves_other_host_and_sets_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            first = root / "first.json"
            second = root / "second.json"
            update = root / "update.json"
            self.write_json(first, self.proposal("host-a", "old"))
            self.write_json(second, self.proposal("host-b", "stable"))
            self.apply(config, first)
            self.apply(config, second)
            changed = self.proposal("host-a", "new", None)
            changed["host_override"] = "host-a"
            self.write_json(update, changed)
            status, _, stderr = self.apply(config, update)
            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.profiles("stable"), saved["hosts"]["host-b"]["profiles"])
            self.assertIsNone(saved["hosts"]["host-a"]["transcripts_directory"])
            self.assertEqual("host-a", saved["host_override"])

    def test_invalid_proposal_leaves_existing_config_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            good = root / "good.json"
            bad = root / "bad.json"
            self.write_json(good, self.proposal("host-a", "stable"))
            self.apply(config, good)
            original = config.read_bytes()
            invalid = self.proposal("host-b", "candidate")
            del invalid["profiles"]["bug-worker"]
            self.write_json(bad, invalid)
            status, _, stderr = self.apply(config, bad)
            self.assertEqual(2, status)
            self.assertIn("proposal.profiles is missing: bug-worker", stderr)
            self.assertEqual(original, config.read_bytes())

    def test_relative_transcript_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            self.write_json(proposal, self.proposal("host-a", "candidate", "relative/transcripts"))
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("must be an absolute path or null", stderr)
            self.assertFalse(config.exists())

    def test_inherit_parent_model_rejects_concrete_effort(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("host-a", "candidate")
            invalid["profiles"]["fast-explorer"] = {"model": "inherit-parent", "effort": "xhigh"}
            self.write_json(proposal, invalid)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("effort must be inherit-parent", stderr)
            self.assertFalse(config.exists())

    def test_schema_version_stays_two_and_unsupported_version_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            existing = CONFIGURE.default_config()
            existing["schema_version"] = 3
            self.write_json(config, existing)
            original = config.read_bytes()
            self.write_json(proposal, self.proposal("host-a", "candidate"))
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("config.schema_version must be 2; found 3", stderr)
            self.assertEqual(original, config.read_bytes())

    def test_replace_failure_preserves_previous_file_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            original = CONFIGURE.default_config()
            self.write_json(config, original)
            changed = CONFIGURE.default_config()
            changed["host_override"] = "host-a"
            with mock.patch.object(CONFIGURE.os, "replace", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(OSError, "blocked"):
                    CONFIGURE.write_atomic(config, changed)
            self.assertEqual(original, json.loads(config.read_text(encoding="utf-8")))
            self.assertEqual([], list(root.glob(".config.*.tmp")))


if __name__ == "__main__":
    unittest.main()
