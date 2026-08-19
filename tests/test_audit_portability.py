#!/usr/bin/env python3

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_portability.py"
SPEC = importlib.util.spec_from_file_location("audit_portability", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class PortabilityAuditTests(unittest.TestCase):
    def make_skill(self, root: Path, body: str, extra=None) -> Path:
        skill = root / "sample"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: sample\ndescription: sample skill\n---\n\n" + body,
            encoding="utf-8",
        )
        for name, content in (extra or {}).items():
            path = skill / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return skill

    def messages(self, skill: Path):
        return [finding.message for finding in AUDIT.check_skill(skill)]

    def test_good_skill_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "| Capability | Use | Fallback |\n"
                "| --- | --- | --- |\n"
                "| `explore` | Trace code. | The parent traces code. |\n\n"
                "Read `references/prompt.md`.\n",
                {"references/prompt.md": "Use `explore` to trace code.\n"},
            )
            self.assertEqual([], self.messages(skill))

    def test_provider_leakage_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Call Cursor with subagent_type: explorer.\n")
            messages = self.messages(skill)
            self.assertIn("provider name", messages)
            self.assertIn("provider helper schema", messages)

    def test_missing_fallback_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Use `parallel` for two passes.\n")
            self.assertIn("capability 'parallel' has no explicit fallback row", self.messages(skill))

    def test_missing_asset_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read `references/missing.md`.\n")
            self.assertIn("missing referenced asset 'references/missing.md'", self.messages(skill))

    def test_model_role_binding_requires_capability_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Use `model_role:deep-judgment`.\n")
            self.assertIn("capability 'model_role' has no explicit fallback row", self.messages(skill))

    def test_legacy_brand_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Load the old pstack router.\n")
            self.assertIn("legacy dstack brand", self.messages(skill))

    def test_missing_markdown_link_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read [the rubric](references/rubric.md).\n")
            self.assertIn("missing markdown link target 'references/rubric.md'", self.messages(skill))

    def test_missing_sibling_skill_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read `../missing/SKILL.md`.\n")
            self.assertIn("missing sibling skill '../missing/SKILL.md'", self.messages(skill))

    def test_orphan_asset_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Nothing points at the runtime notes.\n",
                {"references/runtime.md": "Read the capability contract.\n"},
            )
            self.assertIn("asset is never referenced by the skill", self.messages(skill))

    def test_asset_referenced_from_a_sibling_asset_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Read `references/prompt.md`.\n",
                {
                    "references/prompt.md": "Append `sources/incident.md` when the code is defensive.\n",
                    "references/sources/incident.md": "Search postmortems.\n",
                },
            )
            self.assertEqual([], self.messages(skill))

    def test_directory_reference_covers_its_files(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Follow the shape in [`references/example/`](references/example/).\n",
                {
                    "references/example/README.md": "Index.\n",
                    "references/example/search.md": "One feature.\n",
                },
            )
            self.assertEqual([], self.messages(skill))

    def test_file_inside_a_directory_does_not_cover_its_siblings(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Read `references/sources/incident.md`.\n",
                {
                    "references/sources/incident.md": "Search postmortems.\n",
                    "references/sources/archaeology.md": "Search git history.\n",
                },
            )
            self.assertEqual(
                ["asset is never referenced by the skill"], self.messages(skill)
            )


if __name__ == "__main__":
    unittest.main()
