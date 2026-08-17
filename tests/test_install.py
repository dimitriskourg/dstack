#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("dstack_install", SCRIPT)
assert SPEC and SPEC.loader
INSTALL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INSTALL
SPEC.loader.exec_module(INSTALL)


class InstallerTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "source"
        for name in ("alpha", "beta"):
            skill = source / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: {}\ndescription: test\n---\n".format(name),
                encoding="utf-8",
            )
        bundled_script = source / "skills" / "alpha" / "scripts" / "configure.py"
        bundled_script.parent.mkdir()
        bundled_script.write_text("print('configured')\n", encoding="utf-8")
        for name in ("adapters", "contracts", "schemas"):
            directory = source / name
            directory.mkdir(parents=True)
            (directory / "content.txt").write_text(name, encoding="utf-8")
        (source / "LICENSE").write_text("license\n", encoding="utf-8")
        (source / "NOTICE.md").write_text("notice\n", encoding="utf-8")
        return source

    def run_installer(self, source: Path, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(INSTALL, "SOURCE_ROOT", source):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = INSTALL.run(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def destinations(self, root: Path):
        return [
            "--skills-dir",
            str(root / "agents" / "skills"),
            "--dstack-home",
            str(root / "dstack-home"),
            "--claude-skills-dir",
            str(root / "claude" / "skills"),
        ]

    def test_dry_run_lists_operations_without_creating_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)

            status, stdout, stderr = self.run_installer(
                source, ["--dry-run", "--with-claude-links"] + self.destinations(root)
            )

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertIn("Would copy:", stdout)
            self.assertIn("Would link:", stdout)
            self.assertIn("no files changed", stdout)
            self.assertFalse((root / "agents").exists())
            self.assertFalse((root / "dstack-home").exists())
            self.assertFalse((root / "claude").exists())

    def test_install_copies_skills_and_support_files_and_creates_requested_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)

            status, stdout, stderr = self.run_installer(
                source, ["--with-claude-links"] + self.destinations(root)
            )

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertIn("Installed dstack: 9 operations completed.", stdout)
            self.assertTrue((root / "agents" / "skills" / "alpha" / "SKILL.md").is_file())
            self.assertTrue(
                (
                    root
                    / "agents"
                    / "skills"
                    / "alpha"
                    / "scripts"
                    / "configure.py"
                ).is_file()
            )
            self.assertTrue((root / "dstack-home" / "adapters" / "content.txt").is_file())
            self.assertTrue((root / "dstack-home" / "LICENSE").is_file())
            link = root / "claude" / "skills" / "alpha"
            self.assertTrue(link.is_symlink())
            self.assertEqual(
                (root / "agents" / "skills" / "alpha").resolve(),
                Path(os.readlink(str(link))).resolve(),
            )

    def test_existing_destination_stops_every_operation_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            collision = root / "agents" / "skills" / "beta"
            collision.mkdir(parents=True)
            marker = collision / "owner.txt"
            marker.write_text("unmanaged\n", encoding="utf-8")

            status, stdout, stderr = self.run_installer(source, self.destinations(root))

            self.assertEqual(2, status)
            self.assertEqual("", stdout)
            self.assertIn(str(collision), stderr)
            self.assertIn("No files changed.", stderr)
            self.assertEqual("unmanaged\n", marker.read_text(encoding="utf-8"))
            self.assertFalse((root / "agents" / "skills" / "alpha").exists())
            self.assertFalse((root / "dstack-home").exists())

    def test_dry_run_reports_complete_plan_and_collisions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            collision = root / "agents" / "skills" / "beta"
            collision.mkdir(parents=True)

            status, stdout, stderr = self.run_installer(
                source, ["--dry-run"] + self.destinations(root)
            )

            self.assertEqual(2, status)
            self.assertEqual(7, stdout.count("Would copy:"))
            self.assertIn(str(collision), stderr)
            self.assertIn("a real installation would stop", stderr)
            self.assertFalse((root / "agents" / "skills" / "alpha").exists())
            self.assertFalse((root / "dstack-home").exists())

    def test_broken_claude_link_is_a_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            link = root / "claude" / "skills" / "alpha"
            link.parent.mkdir(parents=True)
            link.symlink_to(root / "missing")

            status, _, stderr = self.run_installer(
                source, ["--with-claude-links"] + self.destinations(root)
            )

            self.assertEqual(2, status)
            self.assertIn(str(link), stderr)
            self.assertTrue(link.is_symlink())
            self.assertFalse((root / "agents").exists())

    def test_existing_dstack_home_is_allowed_when_managed_destinations_are_free(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.make_source(root)
            dstack_home = root / "dstack-home"
            dstack_home.mkdir()
            config = dstack_home / "config.json"
            config.write_text('{"schema_version": 1}\n', encoding="utf-8")

            status, _, stderr = self.run_installer(source, self.destinations(root))

            self.assertEqual(0, status)
            self.assertEqual("", stderr)
            self.assertEqual(
                '{"schema_version": 1}\n', config.read_text(encoding="utf-8")
            )
            self.assertFalse((root / "claude").exists())


if __name__ == "__main__":
    unittest.main()
