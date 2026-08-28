#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "uninstall.py"
SPEC = importlib.util.spec_from_file_location("dstack_uninstall", SCRIPT)
assert SPEC and SPEC.loader
UNINSTALL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = UNINSTALL
SPEC.loader.exec_module(UNINSTALL)


class UninstallerTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "source"
        for name in ("alpha", "beta"):
            skill = source / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: {}\ndescription: test\n---\n".format(name), encoding="utf-8"
            )
        return source

    def install_fixture(self, root: Path):
        skills = root / "agents" / "skills"
        claude = root / "claude" / "skills"
        dstack_home = root / "dstack-home"
        workers = root / "workers"
        for name in ("alpha", "beta"):
            skill = skills / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: {}\ndescription: installed\n---\n".format(name), encoding="utf-8"
            )
            claude.mkdir(parents=True, exist_ok=True)
            (claude / name).symlink_to(skill, target_is_directory=True)
        workers.mkdir()
        for profile in UNINSTALL.PROFILES:
            (workers / "dstack-{}.md".format(profile)).write_text(
                "---\nname: dstack-{0}\ndescription: worker\n---\n\n"
                "<!-- dstack-managed-worker: {0} -->\n".format(profile),
                encoding="utf-8",
            )
        dstack_home.mkdir()
        (dstack_home / "config.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "hosts": {
                        "claude": {
                            "worker_binding": {
                                "mechanism": "worker-definitions",
                                "definitions_directory": str(workers),
                            }
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        (dstack_home / "keep-for-skills-only.txt").write_text("config", encoding="utf-8")
        return skills, claude, dstack_home, workers

    def run_uninstaller(self, source: Path, root: Path, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        destinations = [
            "--skills-dir",
            str(root / "agents" / "skills"),
            "--claude-skills-dir",
            str(root / "claude" / "skills"),
        ]
        with mock.patch.object(UNINSTALL, "SOURCE_ROOT", source), mock.patch.object(
            UNINSTALL, "DSTACK_DIRECTORY", root / "dstack-home"
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = UNINSTALL.run(arguments + destinations)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, claude, dstack_home, workers = self.install_fixture(root)

            status, stdout, stderr = self.run_uninstaller(source, root, ["--all", "--dry-run"])

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertIn("Uninstall dry run complete: 9 removals", stdout)
            self.assertTrue((skills / "alpha").is_dir())
            self.assertTrue((claude / "alpha").is_symlink())
            self.assertTrue(dstack_home.is_dir())
            self.assertTrue((workers / "dstack-fast-explorer.md").is_file())

    def test_skills_only_preserves_configuration_and_workers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, claude, dstack_home, workers = self.install_fixture(root)

            status, stdout, stderr = self.run_uninstaller(source, root, ["--skills-only"])

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertIn("Uninstalled dstack skills only: 4 removals completed.", stdout)
            self.assertFalse((skills / "alpha").exists())
            self.assertFalse(os.path.lexists(str(claude / "alpha")))
            self.assertTrue((dstack_home / "config.json").is_file())
            self.assertTrue((workers / "dstack-fast-explorer.md").is_file())

    def test_all_removes_skills_workers_and_dstack_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, claude, dstack_home, workers = self.install_fixture(root)
            unrelated_skill = skills / "personal"
            unrelated_skill.mkdir()
            unrelated_worker = workers / "personal.md"
            unrelated_worker.write_text("keep", encoding="utf-8")

            status, stdout, stderr = self.run_uninstaller(source, root, ["--all"])

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertIn("Uninstalled dstack skills and configuration: 9 removals completed.", stdout)
            self.assertTrue(unrelated_skill.is_dir())
            self.assertTrue(unrelated_worker.is_file())
            self.assertFalse(dstack_home.exists())
            self.assertFalse((workers / "dstack-fast-explorer.md").exists())

    def test_unverified_skill_stops_before_any_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, claude, dstack_home, _ = self.install_fixture(root)
            (skills / "beta" / "SKILL.md").write_text(
                "---\nname: personal\ndescription: do not remove\n---\n", encoding="utf-8"
            )

            status, stdout, stderr = self.run_uninstaller(source, root, ["--all"])

            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn("ownership cannot be verified", stderr)
            self.assertIn("No files changed.", stderr)
            self.assertTrue((skills / "alpha").is_dir())
            self.assertTrue((claude / "alpha").is_symlink())
            self.assertTrue(dstack_home.is_dir())

    def test_foreign_claude_entry_stops_before_any_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, claude, _, _ = self.install_fixture(root)
            (claude / "alpha").unlink()
            (claude / "alpha").mkdir()

            status, stdout, stderr = self.run_uninstaller(source, root, ["--skills-only"])

            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn("expected a dstack compatibility link", stderr)
            self.assertTrue((skills / "alpha").is_dir())

    def test_tampered_worker_stops_before_any_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, _, dstack_home, workers = self.install_fixture(root)
            (workers / "dstack-bug-worker.md").write_text("personal", encoding="utf-8")

            status, stdout, stderr = self.run_uninstaller(source, root, ["--all"])

            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn("worker definition ownership cannot be verified", stderr)
            self.assertTrue((skills / "alpha").is_dir())
            self.assertTrue(dstack_home.is_dir())

    def test_removal_failure_reports_partial_completion_truthfully(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            skills, _, _, _ = self.install_fixture(root)
            real_remove = UNINSTALL.remove
            calls = []

            def fail_second(removal):
                calls.append(removal)
                if len(calls) == 2:
                    raise OSError("simulated failure")
                real_remove(removal)

            with mock.patch.object(UNINSTALL, "remove", side_effect=fail_second):
                status, stdout, stderr = self.run_uninstaller(
                    source, root, ["--skills-only"]
                )

            self.assertEqual(1, status)
            self.assertEqual(1, stdout.count("Removed "))
            self.assertIn("incomplete after 1 of 4 removals", stderr)
            self.assertNotIn("No files changed", stderr)
            self.assertTrue((skills / "alpha").is_dir())


if __name__ == "__main__":
    unittest.main()
