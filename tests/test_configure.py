#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import os
import subprocess
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
GIT_TMP = Path(__file__).resolve().parent / ".tmp"


class ConfiguratorTests(unittest.TestCase):
    def profiles(self, prefix: str, host: str = "codex"):
        if host == "cursor":
            return {
                profile: {"model": "{}-{}[effort=medium]".format(prefix, profile)}
                for profile in CONFIGURE.PROFILES
            }
        return {
            profile: {"model": "{}-{}".format(prefix, profile), "effort": "medium"}
            for profile in CONFIGURE.PROFILES
        }

    def proposal(
        self,
        host: str,
        prefix: str,
        transcripts: str = "/tmp/transcripts",
        invalid_bindings=None,
        repository_root: str = "/private/tmp/repository",
    ):
        return {
            "host": host,
            "repository_root": repository_root,
            "profiles": self.profiles(prefix, host),
            "invalid_bindings": invalid_bindings or [],
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
            self.assertEqual(self.profiles("stable", "claude"), saved["hosts"]["claude"]["profiles"])
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
            for field, value in (
                ("model", "inherit-parent"),
                ("model", "inherit"),
                ("model", "auto"),
                ("effort", "inherit-parent"),
                ("effort", "inherit"),
                ("effort", "auto"),
            ):
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

    def test_schema_version_is_three_and_unsupported_version_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            existing = CONFIGURE.default_config()
            existing["schema_version"] = 4
            self.write_json(config, existing)
            original = config.read_bytes()
            self.write_json(proposal, self.proposal("codex", "candidate"))
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("config.schema_version must be 3; found 4", stderr)
            self.assertEqual(original, config.read_bytes())

    def test_old_v2_config_fails_with_rerun_setup_guidance(self):
        old_entry = {
            "profiles": self.profiles("old"),
            "invalid_bindings": [],
            "worker_binding": {"mechanism": "spawn-arguments", "definitions_directory": None, "pair_encoding": None},
            "repositories": {},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            self.write_json(config, {"schema_version": 2, "hosts": {"codex": old_entry}})
            original = config.read_bytes()
            self.write_json(proposal, self.proposal("codex", "candidate"))
            for arguments in (
                ["apply", "--proposal", str(proposal)],
                ["resolve", "--host", "codex"],
                ["validate"],
                ["show"],
            ):
                with self.subTest(command=arguments[0]):
                    status, stdout, stderr = self.run_configurator(arguments, config)
                    self.assertEqual(2, status)
                    self.assertEqual("", stdout)
                    self.assertIn("old schema_version 2 config from the worker binding era", stderr)
                    self.assertIn("delete or rewrite ~/.dstack/config.json, then rerun setup-dstack", stderr)
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

    def test_each_host_stores_the_shape_its_spawn_call_takes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            for host, prefix in (("codex", "alpha"), ("claude", "beta"), ("cursor", "gamma")):
                proposal = root / "{}.json".format(host)
                self.write_json(proposal, self.proposal(host, prefix))
                status, _, stderr = self.apply(config, proposal)
                self.assertEqual(0, status, stderr)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(
                {"model": "alpha-fast-explorer", "effort": "medium"},
                saved["hosts"]["codex"]["profiles"]["fast-explorer"],
            )
            self.assertEqual(
                {"model": "beta-fast-explorer", "effort": "medium"},
                saved["hosts"]["claude"]["profiles"]["fast-explorer"],
            )
            self.assertEqual(
                {"model": "gamma-fast-explorer[effort=medium]"},
                saved["hosts"]["cursor"]["profiles"]["fast-explorer"],
            )
            for host in ("codex", "claude", "cursor"):
                self.assertEqual(
                    {"profiles", "invalid_bindings", "repositories"}, set(saved["hosts"][host])
                )

    def test_cursor_accepts_a_catalog_slug_as_the_spawn_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            value = self.proposal("cursor", "unused")
            value["profiles"]["fast-explorer"] = {"model": "vendor-model-low"}
            self.write_json(proposal, value)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(0, status, stderr)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(
                {"model": "vendor-model-low"}, saved["hosts"]["cursor"]["profiles"]["fast-explorer"]
            )

    def test_retired_worker_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("codex", "candidate")
            invalid["worker_binding"] = {
                "mechanism": "spawn-arguments",
                "definitions_directory": None,
                "pair_encoding": None,
            }
            self.write_json(proposal, invalid)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal has unknown keys: worker_binding", stderr)
            self.assertFalse(config.exists())

            entry = self.proposal("codex", "stable")
            stored = {
                "profiles": entry["profiles"],
                "invalid_bindings": [],
                "worker_binding": invalid["worker_binding"],
                "repositories": {},
            }
            self.write_json(config, {"schema_version": 3, "hosts": {"codex": stored}})
            status, _, stderr = self.run_configurator(["validate"], config)
            self.assertEqual(2, status)
            self.assertIn("config.hosts.codex has unknown keys: worker_binding", stderr)

    def test_pair_hosts_require_both_model_and_effort(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for host in ("codex", "claude"):
                with self.subTest(host=host):
                    config = root / "{}.config.json".format(host)
                    proposal = root / "{}.proposal.json".format(host)
                    invalid = self.proposal(host, "candidate")
                    del invalid["profiles"]["bug-worker"]["effort"]
                    self.write_json(proposal, invalid)
                    status, _, stderr = self.apply(config, proposal)
                    self.assertEqual(2, status)
                    self.assertIn("proposal.profiles.bug-worker is missing: effort", stderr)
                    self.assertFalse(config.exists())

    def test_cursor_rejects_a_separate_effort_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            invalid = self.proposal("cursor", "candidate")
            invalid["profiles"]["bug-worker"] = {"model": "vendor-model", "effort": "high"}
            self.write_json(proposal, invalid)
            status, _, stderr = self.apply(config, proposal)
            self.assertEqual(2, status)
            self.assertIn("proposal.profiles.bug-worker has unknown keys: effort", stderr)
            self.assertFalse(config.exists())

    def test_cursor_model_must_be_concrete_and_use_only_the_effort_bracket(self):
        cases = (
            ("auto", "must be a concrete value"),
            ("inherit", "must be a concrete value"),
            ("inherit-parent", "must be a concrete value"),
            ("auto[effort=high]", "must be a concrete value"),
            ("vendor-model[effort=inherit]", "must be a concrete value"),
            ("vendor-model[]", "brackets must be exactly [effort=<value>]"),
            ("vendor-model[fast=false]", "brackets must be exactly [effort=<value>]"),
            ("vendor-model[effort=high,context=300k]", "brackets must be exactly [effort=<value>]"),
            ("vendor-model[effort=]", "brackets must be exactly [effort=<value>]"),
            ("vendor model", "without whitespace"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, (model, expected) in enumerate(cases):
                with self.subTest(model=model):
                    config = root / "{}.config.json".format(index)
                    proposal = root / "{}.proposal.json".format(index)
                    invalid = self.proposal("cursor", "candidate")
                    invalid["profiles"]["skeptical-reviewer"] = {"model": model}
                    self.write_json(proposal, invalid)
                    status, _, stderr = self.apply(config, proposal)
                    self.assertEqual(2, status)
                    self.assertIn(expected, stderr)
                    self.assertFalse(config.exists())

    def test_invalid_bindings_follow_the_host_profile_shape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            proposal = root / "proposal.json"
            retired = [{"model": "retired-model[effort=high]"}]
            self.write_json(proposal, self.proposal("cursor", "current", invalid_bindings=retired))
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.assertEqual(
                retired,
                json.loads(config.read_text(encoding="utf-8"))["hosts"]["cursor"]["invalid_bindings"],
            )

            mismatched = root / "mismatched.json"
            self.write_json(
                mismatched,
                self.proposal("codex", "current", invalid_bindings=[{"model": "retired-model"}]),
            )
            status, _, stderr = self.apply(config, mismatched)
            self.assertEqual(2, status)
            self.assertIn("proposal.invalid_bindings[0] is missing: effort", stderr)

    def test_fused_identifiers_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for field, value in (
                ("model", "claude-fable-5[effort=medium]"),
                ("effort", "medium[extra]"),
            ):
                with self.subTest(field=field, value=value):
                    config = root / "{}.config.json".format(field)
                    proposal = root / "{}.proposal.json".format(field)
                    invalid = self.proposal("codex", "candidate")
                    invalid["profiles"]["fast-explorer"][field] = value
                    self.write_json(proposal, invalid)
                    status, _, stderr = self.apply(config, proposal)
                    self.assertEqual(2, status)
                    self.assertIn("must not contain brackets", stderr)
                    self.assertFalse(config.exists())

    def git_workspace(self):
        GIT_TMP.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=str(GIT_TMP))

    def git(self, repo: Path, *arguments: str) -> None:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo,
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(repo)},
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr.strip() or completed.stdout)

    def init_repo(self, repo: Path) -> str:
        repo.mkdir(parents=True)
        self.git(repo, "init", "--template=", "-b", "main")
        self.git(repo, "config", "user.email", "test@example.com")
        self.git(repo, "config", "user.name", "Test")
        (repo / "README").write_text("repo\n", encoding="utf-8")
        self.git(repo, "add", "README")
        self.git(repo, "commit", "-m", "init")
        return str(repo.resolve())

    def test_resolve_matches_the_registered_checkout(self):
        with self.git_workspace() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            config = root / "config.json"
            proposal = root / "proposal.json"
            repository_root = self.init_repo(repo)
            self.write_json(
                proposal,
                self.proposal("cursor", "live", "/tmp/transcripts", repository_root=repository_root),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            status, stdout, stderr = self.run_configurator(
                ["resolve", "--host", "cursor", "--checkout", repository_root],
                config,
            )
            self.assertEqual(0, status, stderr)
            selected = json.loads(stdout)
            self.assertEqual("exact", selected["match"])
            self.assertEqual(repository_root, selected["repository_root"])
            self.assertEqual(repository_root, selected["checkout_root"])
            self.assertEqual("/tmp/transcripts", selected["transcripts_directory"])

    def test_resolve_accepts_a_linked_worktree_of_a_registered_checkout(self):
        with self.git_workspace() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            worktree = root / "worktree"
            config = root / "config.json"
            proposal = root / "proposal.json"
            repository_root = self.init_repo(repo)
            self.git(repo, "worktree", "add", "-b", "feature", str(worktree))
            self.write_json(
                proposal,
                self.proposal("cursor", "live", "/tmp/transcripts", repository_root=repository_root),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            status, stdout, stderr = self.run_configurator(
                ["resolve", "--host", "cursor", "--checkout", str(worktree)],
                config,
            )
            self.assertEqual(0, status, stderr)
            selected = json.loads(stdout)
            self.assertEqual("linked-worktree", selected["match"])
            self.assertEqual(repository_root, selected["repository_root"])
            self.assertEqual(str(worktree.resolve()), selected["checkout_root"])
            self.assertEqual("/tmp/transcripts", selected["transcripts_directory"])

    def test_resolve_prefers_the_primary_worktree_when_several_checkouts_are_registered(self):
        with self.git_workspace() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            first = root / "first"
            second = root / "second"
            config = root / "config.json"
            proposal = root / "proposal.json"
            repository_root = self.init_repo(repo)
            self.git(repo, "worktree", "add", "-b", "one", str(first))
            self.git(repo, "worktree", "add", "-b", "two", str(second))
            self.write_json(
                proposal,
                self.proposal("cursor", "main", "/tmp/main-transcripts", repository_root=repository_root),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            self.write_json(
                proposal,
                self.proposal(
                    "cursor",
                    "main",
                    "/tmp/first-transcripts",
                    repository_root=str(first.resolve()),
                ),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            status, stdout, stderr = self.run_configurator(
                ["resolve", "--host", "cursor", "--checkout", str(second)],
                config,
            )
            self.assertEqual(0, status, stderr)
            selected = json.loads(stdout)
            self.assertEqual("linked-worktree", selected["match"])
            self.assertEqual(repository_root, selected["repository_root"])
            self.assertEqual("/tmp/main-transcripts", selected["transcripts_directory"])

    def test_resolve_rejects_a_different_git_repository(self):
        with self.git_workspace() as temporary:
            root = Path(temporary)
            registered = root / "registered"
            other = root / "other"
            config = root / "config.json"
            proposal = root / "proposal.json"
            repository_root = self.init_repo(registered)
            self.init_repo(other)
            self.write_json(
                proposal,
                self.proposal("cursor", "live", "/tmp/transcripts", repository_root=repository_root),
            )
            self.assertEqual(0, self.apply(config, proposal)[0])
            status, stdout, stderr = self.run_configurator(
                ["resolve", "--host", "cursor", "--checkout", str(other)],
                config,
            )
            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn("only registers `{}`".format(repository_root), stderr)

    def test_resolve_requires_an_existing_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            status, stdout, stderr = self.run_configurator(
                ["resolve", "--host", "cursor"],
                config,
            )
            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn("configuration file does not exist: {}".format(config.resolve()), stderr)


if __name__ == "__main__":
    unittest.main()
