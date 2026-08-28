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

    def proposal(
        self,
        host: str,
        prefix: str,
        transcripts: str = "/tmp/transcripts",
        worker_binding=None,
        invalid_bindings=None,
        repository_root: str = "/private/tmp/repository",
    ):
        return {
            "host": host,
            "repository_root": repository_root,
            "profiles": self.profiles(prefix),
            "invalid_bindings": invalid_bindings or [],
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

    def test_validate_rejects_missing_config_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            status, stdout, stderr = self.run_configurator(["validate"], config)
            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn("configuration file does not exist: {}".format(config.resolve()), stderr)
            self.assertFalse(config.exists())

    def test_validate_accepts_an_existing_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            self.write_json(config, CONFIGURE.default_config())
            status, stdout, stderr = self.run_configurator(["validate"], config)
            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertIn("Valid dstack configuration: {}".format(config.resolve()), stdout)

    def test_host_settings_and_transcript_paths_coexist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            first = root / "first.json"
            second = root / "second.json"
            self.write_json(first, self.proposal("codex", "alpha", "/tmp/a-transcripts"))
            self.write_json(second, self.proposal("claude", "beta", "/tmp/b-transcripts"))
            self.assertEqual(0, self.apply(config, first)[0])
            self.assertEqual(0, self.apply(config, second)[0])
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.profiles("alpha"), saved["hosts"]["codex"]["profiles"])
            self.assertEqual(
                "/tmp/b-transcripts",
                saved["hosts"]["claude"]["repositories"]["/private/tmp/repository"]["transcripts_directory"],
            )

    def test_update_preserves_other_host(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            first = root / "first.json"
            second = root / "second.json"
            update = root / "update.json"
            self.write_json(first, self.proposal("codex", "old"))
            self.write_json(second, self.proposal("claude", "stable"))
            self.apply(config, first)
            self.apply(config, second)
            changed = self.proposal("codex", "new", None)
            self.write_json(update, changed)
            status, _, stderr = self.apply(config, update)
            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(self.profiles("stable"), saved["hosts"]["claude"]["profiles"])
            self.assertIsNone(
                saved["hosts"]["codex"]["repositories"]["/private/tmp/repository"]["transcripts_directory"]
            )
            self.assertNotIn("host_override", saved)

    def test_reconciled_invalid_bindings_survive_apply_until_restored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            unavailable = [{"model": "retired-model", "effort": "medium"}]

            self.write_json(
                proposal,
                self.proposal("codex", "replacement", invalid_bindings=unavailable),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.assertEqual(
                unavailable,
                json.loads(config.read_text(encoding="utf-8"))["hosts"]["codex"]["invalid_bindings"],
            )

            self.write_json(
                proposal,
                self.proposal("codex", "replacement", "/tmp/refreshed", invalid_bindings=unavailable),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.assertEqual(
                unavailable,
                json.loads(config.read_text(encoding="utf-8"))["hosts"]["codex"]["invalid_bindings"],
            )

            self.write_json(proposal, self.proposal("codex", "restored", invalid_bindings=[]))
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.assertEqual(
                [],
                json.loads(config.read_text(encoding="utf-8"))["hosts"]["codex"]["invalid_bindings"],
            )

    def test_host_override_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("codex", "candidate")
            invalid["host_override"] = "claude"
            self.write_json(proposal, invalid)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal has unknown keys: host_override", stderr)
            self.assertFalse(config.exists())

    def test_only_canonical_host_ids_are_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            self.write_json(proposal, self.proposal("auto", "candidate"))
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal.host must be one of: codex, claude, cursor", stderr)
            self.assertFalse(config.exists())

    def test_invalid_proposal_leaves_existing_config_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            good = root / "good.json"
            bad = root / "bad.json"
            self.write_json(good, self.proposal("codex", "stable"))
            self.apply(config, good)
            original = config.read_bytes()
            invalid = self.proposal("claude", "candidate")
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
            self.write_json(proposal, self.proposal("codex", "candidate", "relative/transcripts"))
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("must be an absolute path or null", stderr)
            self.assertFalse(config.exists())

    def test_repository_transcripts_survive_a_b_a_switching(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            repository_a = str((root / "repository-a").resolve())
            repository_b = str((root / "repository-b").resolve())

            self.write_json(
                proposal,
                self.proposal("codex", "first", "/tmp/a-transcripts", repository_root=repository_a),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.write_json(
                proposal,
                self.proposal("codex", "second", "/tmp/b-transcripts", repository_root=repository_b),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.write_json(
                proposal,
                self.proposal("codex", "third", "/tmp/a-transcripts", repository_root=repository_a),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])

            repositories = json.loads(config.read_text(encoding="utf-8"))["hosts"]["codex"]["repositories"]
            self.assertEqual("/tmp/a-transcripts", repositories[repository_a]["transcripts_directory"])
            self.assertEqual("/tmp/b-transcripts", repositories[repository_b]["transcripts_directory"])
            self.assertEqual(repository_a, repositories[repository_a]["repository_root"])

    def test_noncanonical_repository_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            self.write_json(
                proposal,
                self.proposal("codex", "candidate", repository_root="/private/tmp/../tmp/repository"),
            )
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal.repository_root must be canonical", stderr)
            self.assertFalse(config.exists())

    def test_repository_entry_must_match_its_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            entry = self.proposal("codex", "candidate")
            entry.pop("host")
            entry.pop("repository_root")
            config_value = CONFIGURE.default_config()
            config_value["hosts"]["codex"] = {
                "profiles": entry["profiles"],
                "invalid_bindings": entry["invalid_bindings"],
                "worker_binding": entry["worker_binding"],
                "repositories": {
                    "/private/tmp/repository": {
                        "repository_root": "/private/tmp/other-repository",
                        "transcripts_directory": entry["transcripts_directory"],
                    }
                },
            }
            self.write_json(config, config_value)
            status, _, stderr = self.run_configurator(["validate"], config)
            self.assertEqual(2, status)
            self.assertIn("repository_root must match its repository key", stderr)

    def test_reserved_binding_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for field, value in (("model", "inherit-parent"), ("model", "auto"), ("effort", "inherit-parent"), ("effort", "auto")):
                with self.subTest(field=field, value=value):
                    config = root / "{}.{}.config.json".format(field, value)
                    proposal = root / "{}.{}.proposal.json".format(field, value)
                    invalid = self.proposal("codex", "candidate")
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
            self.write_json(proposal, self.proposal("codex", "candidate"))
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
            entry = self.proposal("codex", "changed")
            entry.pop("host")
            entry.pop("repository_root")
            changed["hosts"]["codex"] = {
                "profiles": entry["profiles"],
                "invalid_bindings": entry["invalid_bindings"],
                "worker_binding": entry["worker_binding"],
                "repositories": {
                    "/private/tmp/repository": {
                        "repository_root": "/private/tmp/repository",
                        "transcripts_directory": entry["transcripts_directory"],
                    }
                },
            }
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
            self.write_json(first, self.proposal("codex", "alpha"))
            self.write_json(
                second,
                self.proposal(
                    "claude",
                    "beta",
                    worker_binding={"mechanism": "worker-definitions", "definitions_directory": "/tmp/workers"},
                ),
            )
            self.assertEqual(0, self.apply(config, first)[0])
            self.assertEqual(0, self.apply(config, second)[0])
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(
                {"mechanism": "spawn-arguments", "definitions_directory": None},
                saved["hosts"]["codex"]["worker_binding"],
            )
            self.assertEqual(
                {"mechanism": "worker-definitions", "definitions_directory": "/tmp/workers"},
                saved["hosts"]["claude"]["worker_binding"],
            )

    def test_missing_worker_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("codex", "candidate")
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
                    self.write_json(proposal, self.proposal("codex", "candidate", worker_binding=binding))
                    status, _, stderr = self.apply(config, proposal)
                    self.assertEqual(2, status)
                    self.assertIn(expected, stderr)
                    self.assertFalse(config.exists())


if __name__ == "__main__":
    unittest.main()
