#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "adapters" / "codex" / "discover_models.py"
SPEC = importlib.util.spec_from_file_location("dstack_codex_catalog", SCRIPT)
assert SPEC and SPEC.loader
CATALOG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CATALOG
SPEC.loader.exec_module(CATALOG)


class CodexCatalogTests(unittest.TestCase):
    def completed(self, arguments, stdout="", stderr="", status=0):
        return subprocess.CompletedProcess(arguments, status, stdout, stderr)

    def test_discovers_exact_model_effort_pairs(self):
        payload = {
            "models": [
                {
                    "slug": "gpt-example-fast",
                    "supported_reasoning_levels": [
                        {"effort": "low"},
                        {"effort": "xhigh"},
                    ],
                }
            ]
        }
        with mock.patch.object(
            CATALOG,
            "run_codex",
            side_effect=[
                self.completed(["codex"], stdout="models Render the raw model catalog"),
                self.completed(["codex"], stdout=json.dumps(payload)),
            ],
        ):
            self.assertEqual({"gpt-example-fast": ["low", "xhigh"]}, CATALOG.discover())

    def test_unadvertised_command_disables_discovery(self):
        with mock.patch.object(
            CATALOG,
            "run_codex",
            return_value=self.completed(["codex"], stdout="app-server only"),
        ):
            with self.assertRaisesRegex(CATALOG.CatalogError, "does not advertise"):
                CATALOG.discover()

    def test_check_rejects_unsupported_effort(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(CATALOG, "discover", return_value={"model-a": ["medium"]}):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = CATALOG.run(["--check", "model-a", "xhigh"])
        self.assertEqual(2, status)
        self.assertEqual("invalid\n", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
