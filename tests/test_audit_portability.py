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
    SIDECAR = 'interface:\n  display_name: "Sample"\n  short_description: "A sample skill"\n'
    SIDECAR_USER_INVOKED = SIDECAR + "policy:\n  allow_implicit_invocation: false\n"

    def make_skill(self, root: Path, body: str, extra=None, frontmatter="", sidecar=None, name="sample") -> Path:
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: {}\ndescription: sample skill\n".format(name) + frontmatter + "---\n\n" + body,
            encoding="utf-8",
        )
        files = {}
        if sidecar is not False:
            files["agents/openai.yaml"] = self.SIDECAR if sidecar is None else sidecar
        files.update(extra or {})
        for name, content in files.items():
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

    def test_config_dependent_skill_requires_fixed_fail_closed_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Use the configured profiles.\n", name="arena")
            messages = self.messages(skill)
            self.assertIn("config-dependent skill must name the fixed config path", messages)
            self.assertIn("config-dependent skill must select the active harness entry directly", messages)
            self.assertIn("config-dependent skill must fail closed with setup-dstack guidance", messages)
            self.assertIn("profile-consuming skill must require a concrete model and effort pair", messages)

    def test_config_dependent_skill_contract_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Read `~/.dstack/config.json` and select `hosts[<active-harness>]`; on failure, stop and name the exact problem. "
                "Call the Skill tool with `setup-dstack`. Require a concrete model and effort pair.\n",
                name="arena",
            )
            self.assertEqual([], self.messages(skill))

    def test_config_path_override_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read `DSTACK_HOME/config.json`.\n")
            self.assertIn("config path override", self.messages(skill))

    def test_host_selection_override_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read `host_override`.\n")
            self.assertIn("host selection override", self.messages(skill))

    def test_backticked_provider_helper_schema_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "- `subagent_type`: `generalPurpose`\n- `readonly`: `true`\n")
            self.assertIn("provider helper schema", self.messages(skill))

    def test_typescript_readonly_modifier_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "```ts\ntype UserId = string & { readonly __brand: \"UserId\" }\n```\n")
            self.assertEqual([], self.messages(skill))

    def test_exact_skill_call_phrase_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Call the Skill tool with `how`.\n")
            self.assertEqual([], self.messages(skill))

    def test_legacy_skill_directive_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Run the **how** skill over the code.\n")
            self.assertIn("skill directive must use the Skill tool phrase", self.messages(skill))

    def test_user_invoked_skill_with_matching_sidecar_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Do the thing.\n",
                frontmatter="disable-model-invocation: true\n",
                sidecar=self.SIDECAR_USER_INVOKED,
            )
            self.assertEqual([], self.messages(skill))

    def test_frontmatter_without_sidecar_policy_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp), "Do the thing.\n", frontmatter="disable-model-invocation: true\n"
            )
            self.assertIn("sidecar invocation policy disagrees with SKILL.md", self.messages(skill))

    def test_sidecar_policy_without_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp), "Do the thing.\n", sidecar=self.SIDECAR_USER_INVOKED
            )
            self.assertIn("sidecar invocation policy disagrees with SKILL.md", self.messages(skill))

    def test_disable_model_invocation_must_be_true(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp), "Do the thing.\n", frontmatter="disable-model-invocation: false\n"
            )
            self.assertIn("disable-model-invocation must be true or omitted", self.messages(skill))

    def test_unsupported_frontmatter_key_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Do the thing.\n", frontmatter="allowed-tools: Bash\n")
            self.assertIn("unsupported frontmatter key(s): allowed-tools", self.messages(skill))

    def test_missing_sidecar_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Do the thing.\n", sidecar=False)
            self.assertIn("missing Codex sidecar", self.messages(skill))

    def test_sidecar_interface_fields_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Do the thing.\n", sidecar="interface:\n")
            messages = self.messages(skill)
            self.assertIn("sidecar interface.display_name is required", messages)
            self.assertIn("sidecar interface.short_description is required", messages)

    def test_missing_asset_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read `references/missing.md`.\n")
            self.assertIn("missing referenced asset 'references/missing.md'", self.messages(skill))

    def test_legacy_brand_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Load the old pstack router.\n")
            self.assertIn("legacy brand", self.messages(skill))

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
