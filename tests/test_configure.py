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

    def proposal(self, host: str, prefix: str, transcripts: str = "/tmp/transcripts", worker_binding=None):
        return {
            "host": host,
            "profiles": self.profiles(prefix),
            "invalid_bindings": [],
            "worker_binding": worker_binding or {"mechanism": "spawn-arguments", "definitions_directory": None},
            "transcripts_directory": transcripts,
        }

    def write_json(self, path: Path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def run_configurator(self, arguments, config: Path):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(CONFIGURE, "CONFIG_PATH", config):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = CONFIGURE.run(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def apply(self, config: Path, proposal: Path):
        return self.run_configurator(["apply", "--proposal", str(proposal)], config)

    def test_show_uses_implicit_defaults_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            status, stdout, stderr = self.run_configurator(["show"], config)
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

    def test_update_preserves_other_host(self):
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
            self.write_json(update, changed)
            status, _, stderr = self.apply(config, update)
            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.profiles("stable"), saved["hosts"]["host-b"]["profiles"])
            self.assertIsNone(saved["hosts"]["host-a"]["transcripts_directory"])
            self.assertNotIn("host_override", saved)

    def test_host_override_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("host-a", "candidate")
            invalid["host_override"] = "host-b"
            self.write_json(proposal, invalid)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal has unknown keys: host_override", stderr)
            self.assertFalse(config.exists())

    def test_auto_is_not_a_host_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            self.write_json(proposal, self.proposal("auto", "candidate"))
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal.host must be a lowercase host id", stderr)
            self.assertFalse(config.exists())

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

    def test_reserved_binding_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for field, value in (("model", "inherit-parent"), ("model", "auto"), ("effort", "inherit-parent"), ("effort", "auto")):
                with self.subTest(field=field, value=value):
                    config = root / "{}.{}.config.json".format(field, value)
                    proposal = root / "{}.{}.proposal.json".format(field, value)
                    invalid = self.proposal("host-a", "candidate")
                    invalid["profiles"]["fast-explorer"][field] = value
                    self.write_json(proposal, invalid)
                    status, _, stderr = self.apply(config, proposal)
                    self.assertEqual(2, status)
                    self.assertIn("must be a concrete value", stderr)
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
            entry = self.proposal("host-a", "changed")
            entry.pop("host")
            changed["hosts"]["host-a"] = entry
            with mock.patch.object(CONFIGURE.os, "replace", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(OSError, "blocked"):
                    CONFIGURE.write_atomic(config, changed)
            self.assertEqual(original, json.loads(config.read_text(encoding="utf-8")))
            self.assertEqual([], list(root.glob(".config.*.tmp")))

    def test_worker_binding_is_required_and_preserved_per_host(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            first = root / "first.json"
            second = root / "second.json"
            self.write_json(first, self.proposal("host-a", "alpha"))
            self.write_json(
                second,
                self.proposal(
                    "host-b",
                    "beta",
                    worker_binding={"mechanism": "worker-definitions", "definitions_directory": "/tmp/workers"},
                ),
            )
            self.assertEqual(0, self.apply(config, first)[0])
            self.assertEqual(0, self.apply(config, second)[0])
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(
                {"mechanism": "spawn-arguments", "definitions_directory": None},
                saved["hosts"]["host-a"]["worker_binding"],
            )
            self.assertEqual(
                {"mechanism": "worker-definitions", "definitions_directory": "/tmp/workers"},
                saved["hosts"]["host-b"]["worker_binding"],
            )

    def test_missing_worker_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("host-a", "candidate")
            del invalid["worker_binding"]
            self.write_json(proposal, invalid)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal is missing: worker_binding", stderr)
            self.assertFalse(config.exists())

    def test_worker_binding_mechanism_and_directory_must_agree(self):
        cases = (
            ({"mechanism": "inherit", "definitions_directory": None}, "must be one of"),
            ({"mechanism": "worker-definitions", "definitions_directory": None}, "must be an absolute path"),
            ({"mechanism": "worker-definitions", "definitions_directory": "workers"}, "must be an absolute path"),
            ({"mechanism": "spawn-arguments", "definitions_directory": "/tmp/workers"}, "must be null"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, (binding, expected) in enumerate(cases):
                with self.subTest(binding=binding):
                    config = root / "{}.config.json".format(index)
                    proposal = root / "{}.proposal.json".format(index)
                    self.write_json(proposal, self.proposal("host-a", "candidate", worker_binding=binding))
                    status, _, stderr = self.apply(config, proposal)
                    self.assertEqual(2, status)
                    self.assertIn(expected, stderr)
                    self.assertFalse(config.exists())


if __name__ == "__main__":
    unittest.main()
