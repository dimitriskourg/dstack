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


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "setup-dstack" / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location("dstack_" + name, SCRIPTS / "{}.py".format(name))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONFIGURE = load("configure")
BINDINGS = load("worker_bindings")


class WorkerBindingTests(unittest.TestCase):
    def host_entry(self, directory, mechanism="worker-definitions"):
        profiles = {
            profile: {"model": "model-{}".format(profile), "effort": "low"}
            for profile in CONFIGURE.PROFILES
        }
        profiles["skeptical-reviewer"] = {"model": "model-reviewer", "effort": "high"}
        return {
            "profiles": profiles,
            "invalid_bindings": [],
            "worker_binding": {
                "mechanism": mechanism,
                "definitions_directory": str(directory) if directory is not None else None,
            },
            "transcripts_directory": None,
        }

    def write_config(self, config: Path, entry, host="host-a"):
        config.write_text(
            json.dumps({"schema_version": 2, "hosts": {host: entry}}),
            encoding="utf-8",
        )

    def run_bindings(self, arguments, config: Path):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(BINDINGS.configure, "CONFIG_PATH", config):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = BINDINGS.run(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_sync_writes_and_confirms_one_definition_per_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            workers = root / "workers"
            self.write_config(config, self.host_entry(workers))
            status, stdout, stderr = self.run_bindings(["--host", "host-a"], config)
            self.assertEqual(0, status, stderr)
            self.assertEqual(
                sorted("dstack-{}.md".format(profile) for profile in CONFIGURE.PROFILES),
                sorted(path.name for path in workers.iterdir()),
            )
            self.assertEqual(4, stdout.count("created"))
            self.assertIn("all four profiles are pinned", stdout)
            reviewer = (workers / "dstack-skeptical-reviewer.md").read_text(encoding="utf-8")
            self.assertIn("model: model-reviewer\n", reviewer)
            self.assertIn("effort: high\n", reviewer)

    def test_sync_is_idempotent_and_restores_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            workers = root / "workers"
            self.write_config(config, self.host_entry(workers))
            self.run_bindings(["--host", "host-a"], config)
            status, stdout, _ = self.run_bindings(["--host", "host-a"], config)
            self.assertEqual(0, status)
            self.assertEqual(4, stdout.count("unchanged"))
            drifted = workers / "dstack-bug-worker.md"
            drifted.write_text(drifted.read_text(encoding="utf-8").replace("effort: low", "effort: max"), encoding="utf-8")
            status, stdout, _ = self.run_bindings(["--host", "host-a"], config)
            self.assertEqual(0, status)
            self.assertIn("updated dstack-bug-worker.md", stdout)
            self.assertIn("effort: low\n", drifted.read_text(encoding="utf-8"))

    def test_sync_keeps_unrelated_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            workers = root / "workers"
            workers.mkdir()
            unrelated = workers / "reviewer.md"
            unrelated.write_text("Mine.\n", encoding="utf-8")
            self.write_config(config, self.host_entry(workers))
            self.assertEqual(0, self.run_bindings(["--host", "host-a"], config)[0])
            self.assertEqual("Mine.\n", unrelated.read_text(encoding="utf-8"))

    def test_spawn_argument_host_generates_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            self.write_config(config, self.host_entry(None, mechanism="spawn-arguments"))
            status, stdout, _ = self.run_bindings(["--host", "host-a"], config)
            self.assertEqual(0, status)
            self.assertIn("no worker definitions are needed", stdout)

    def test_invalid_configuration_stops_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            workers = root / "workers"
            entry = self.host_entry(workers)
            entry["profiles"]["fast-explorer"]["effort"] = "inherit-parent"
            self.write_config(config, entry)
            status, _, stderr = self.run_bindings(["--host", "host-a"], config)
            self.assertEqual(2, status)
            self.assertIn("must be a concrete value", stderr)
            self.assertFalse(workers.exists())


if __name__ == "__main__":
    unittest.main()
