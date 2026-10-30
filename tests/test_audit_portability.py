#!/usr/bin/env python3

import importlib.util
import json
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

    CONFIG_BODY = (
        "Map the system-provided product identity to `codex`, `claude`, or `cursor`; never invent an alias. "
        "Read `~/.dstack/config.json` and select `hosts[<active-harness>]` and `repositories[<canonical-repository-root>]`, "
        "and verify its `repository_root` exactly matches; if that key is absent, use `git rev-parse --git-common-dir`. "
        "Run `configure.py resolve`; on failure, stop and name the exact problem. "
        "Tell the user to invoke `setup-dstack` explicitly. Require a concrete model and effort pair. "
        "Pass it as the native spawn call takes it: for `codex` and `claude`, `model` and `effort` as "
        "separate spawn arguments; for `cursor`, a `model` that already carries effort. Never inherit session effort. "
        "For transcripts, return `transcripts_directory`.\n"
    )

    def test_config_skill_requires_fixed_fail_closed_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Use the configured profiles.\n", name="dstack-config")
            messages = self.messages(skill)
            for message in (
                "config skill must name the fixed config path",
                "config skill must select the active harness entry directly",
                "config skill must derive a canonical harness id",
                "config skill must reject harness aliases",
                "config skill must select the canonical repository entry",
                "config skill must verify the repository entry identity",
                "config skill must accept linked worktrees via git common directory",
                "config skill must resolve the repository entry with configure.py resolve",
                "config skill must return the transcripts directory",
                "config skill must fail closed with setup-dstack guidance",
                "config skill must require a concrete model and effort pair",
                "config skill must state how each host's spawn call takes the profile",
                "config skill must forbid inheriting session effort",
            ):
                self.assertIn(message, messages)

    def test_config_skill_contract_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), self.CONFIG_BODY, name="dstack-config")
            self.assertEqual([], self.messages(skill))

    def test_config_caller_must_call_dstack_config(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Spawn a judge on the `skeptical-reviewer` profile.\n", name="arena")
            self.assertIn("config-dependent skill must resolve config through dstack-config", self.messages(skill))

    def test_config_caller_with_one_call_line_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Call the Skill tool with `dstack-config`. Name the `skeptical-reviewer` profile. Spawn one judge on it.\n",
                name="arena",
            )
            self.assertEqual([], self.messages(skill))

    def test_other_skill_must_not_redescribe_config_procedure(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Call the Skill tool with `dstack-config`.\n",
                {"references/notes.md": "Select `hosts[<active-harness>]` from `~/.dstack/config.json`.\n"},
                name="arena",
            )
            self.assertIn("config procedure belongs only in dstack-config", self.messages(skill))

    def test_user_guide_may_name_config_path_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_skill(root, "Setup writes `~/.dstack/config.json`.\n", name="dstack-help")
            self.assertEqual([], self.messages(guide))
            leaky = self.make_skill(root / "b", "Skip profiles listed in `invalid_bindings`.\n", name="dstack-help")
            self.assertIn("config procedure belongs only in dstack-config", self.messages(leaky))

    def test_shipped_schema_matches_each_host_spawn_shape(self):
        schema = json.loads((AUDIT.ROOT / "schemas" / "config.schema.json").read_text(encoding="utf-8"))
        self.assertEqual([], AUDIT.schema_findings(schema))

    def test_schema_with_a_worker_binding_or_wrong_host_shape_fails(self):
        schema = json.loads((AUDIT.ROOT / "schemas" / "config.schema.json").read_text(encoding="utf-8"))
        schema["$defs"]["workerBinding"] = {"type": "object"}
        schema["$defs"]["pairHost"]["required"].append("worker_binding")
        schema["$defs"]["cursorBinding"]["required"].append("effort")
        schema["properties"]["hosts"]["properties"]["cursor"] = {"$ref": "#/$defs/pairHost"}
        schema["$defs"]["modelIdentifier"]["not"]["enum"].remove("inherit")
        messages = AUDIT.schema_findings(schema)
        self.assertIn("retired worker binding must stay absent from the schema", messages)
        self.assertIn("pairHost must contain exactly profiles, invalid_bindings, and repositories", messages)
        self.assertIn("cursorBinding must contain exactly model", messages)
        self.assertIn("codex and claude must use pairHost and cursor must use cursorHost", messages)
        self.assertIn("config must reject automatic and parent-inheritance binding aliases", messages)

    def test_retired_worker_binding_terms_fail_in_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Spawn `dstack-<profile>` through `worker_binding`.\n")
            self.assertIn("retired worker binding", self.messages(skill))

    def test_supported_playbook_inventory_is_exact(self):
        playbooks = AUDIT.SKILLS / "dstack-mode" / "playbooks"
        actual = {path.stem for path in playbooks.glob("*.md")}
        self.assertEqual(AUDIT.REQUIRED_DSTACK_PLAYBOOKS, actual)
        self.assertFalse(AUDIT.EXCLUDED_DSTACK_PLAYBOOKS & actual)

    def test_kebab_from_title_keeps_hyphens_and_drops_other_punctuation(self):
        self.assertEqual("laziness-protocol", AUDIT.kebab_from_title("Laziness Protocol"))
        self.assertEqual("opening-a-pr", AUDIT.kebab_from_title("Opening a PR"))
        self.assertEqual(
            "test-behavior-not-implementation",
            AUDIT.kebab_from_title("Test Behavior, Not Implementation"),
        )
        self.assertEqual(
            "multi-phase-or-multi-request-plan",
            AUDIT.kebab_from_title("Multi-phase or multi-request plan"),
        )
        self.assertEqual(
            "apple-development-cleanup",
            AUDIT.kebab_from_title("Apple development cleanup"),
        )
        self.assertEqual(
            "sequence-work-into-verifiable-units",
            AUDIT.kebab_from_title("Sequence Work into Verifiable Units"),
        )

    def test_shipped_mode_index_resolves_by_convention(self):
        findings = [finding.message for finding in AUDIT.check_structure()]
        self.assertFalse(any("does not resolve" in message for message in findings))
        self.assertFalse(any("is not referenced by a resolvable title" in message for message in findings))
        body = (AUDIT.SKILLS / "dstack-mode" / "SKILL.md").read_text(encoding="utf-8")
        principles = {name: title for title, name, _ in AUDIT.resolve_principle_index(body)}
        playbooks = {stem: title for title, stem, _ in AUDIT.resolve_playbook_index(body)}
        self.assertEqual(
            "principle-laziness-protocol",
            "principle-" + AUDIT.kebab_from_title(principles["principle-laziness-protocol"]),
        )
        self.assertEqual(
            "Sequence Work into Verifiable Units",
            principles["principle-sequence-verifiable-units"],
        )
        self.assertNotEqual(
            "principle-sequence-verifiable-units",
            "principle-" + AUDIT.kebab_from_title(principles["principle-sequence-verifiable-units"]),
        )
        self.assertEqual("Investigation", playbooks["investigation"])
        self.assertEqual("Authoring or modifying a skill", playbooks["authoring-a-skill"])
        self.assertNotEqual("authoring-a-skill", AUDIT.kebab_from_title(playbooks["authoring-a-skill"]))
        self.assertEqual(AUDIT.REQUIRED_DSTACK_PLAYBOOKS, set(playbooks))

    def test_unresolved_mode_title_fails(self):
        body = (
            "## Principles\n\n"
            "- **Missing Leaf.** A title with no matching skill.\n\n"
            "## Playbooks\n\n"
            "- **Ghost Playbook.** A title with no matching file.\n"
            "- **Shipping.** An excluded playbook referenced by title.\n"
        )
        messages = [finding.message for finding in AUDIT.check_mode_index(body, set(), set(), "mode.md")]
        self.assertIn(
            "principle title 'Missing Leaf' does not resolve to an existing skill (principle-missing-leaf)",
            messages,
        )
        self.assertIn(
            "playbook title 'Ghost Playbook' does not resolve to an existing playbook (ghost-playbook)",
            messages,
        )
        self.assertIn(
            "playbook title 'Shipping' resolves to excluded playbook 'shipping'",
            messages,
        )
        self.assertTrue(any("supported playbook" in message and "is not referenced" in message for message in messages))

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

    def test_model_disabled_internal_callee_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "Call the Skill tool with `callee`.\n", name="caller")
            self.make_skill(
                root,
                "Do the thing.\n",
                frontmatter="disable-model-invocation: true\n",
                sidecar=self.SIDECAR_USER_INVOKED,
                name="callee",
            )
            messages = [
                finding.message
                for finding in AUDIT.run(root, include_structure=False)
            ]
            self.assertIn(
                "model-disabled skill 'callee' cannot be used as an internal callee",
                messages,
            )

    def test_user_only_guidance_does_not_create_invocation_edge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "Tell the user to invoke `callee` explicitly.\n", name="caller")
            self.make_skill(
                root,
                "Do the thing.\n",
                frontmatter="disable-model-invocation: true\n",
                sidecar=self.SIDECAR_USER_INVOKED,
                name="callee",
            )
            self.assertEqual([], AUDIT.run(root, include_structure=False))

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

    def test_frontmatter_name_must_match_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Do the thing.\n", name="sample")
            (skill / "SKILL.md").write_text(
                "---\nname: other-name\ndescription: sample skill\n---\n\nDo the thing.\n",
                encoding="utf-8",
            )
            self.assertIn("frontmatter name must match the skill directory", self.messages(skill))

    def test_skill_directory_must_be_agent_skills_name(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Do the thing.\n", name="Not A Skill")
            self.assertIn(
                "skill directory must be lowercase words joined by hyphens, at most 64 characters",
                self.messages(skill),
            )

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

    def test_titled_markdown_link_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), 'Read [the rubric](references/rubric.md "Rubric").\n')
            self.assertIn("missing markdown link target 'references/rubric.md'", self.messages(skill))

    def test_angle_bracket_markdown_link_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(Path(temp), "Read [the rubric](<references/rubric.md>).\n")
            self.assertIn("missing markdown link target 'references/rubric.md'", self.messages(skill))

    def test_js_import_regex_is_not_a_markdown_link(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Run `scripts/tool.mjs`.\n",
                {
                    "scripts/tool.mjs": (
                        'const imports = (text, dir) =>\n'
                        '  [...text.matchAll(/\\b(?:from|import)\\s*\\(?\\s*["\'](\\.{1,2}\\/[^"\']+)["\']/g)];\n'
                    ),
                },
            )
            self.assertEqual([], self.messages(skill))

    def test_python_bytecode_is_not_a_skill_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Run `scripts/tool.py`.\n",
                {"scripts/tool.py": "print(1)\n"},
            )
            cache = skill / "scripts" / "__pycache__"
            cache.mkdir()
            (cache / "tool.cpython-312.pyc").write_bytes(b"\0")
            (skill / "scripts" / "tool.pyc").write_bytes(b"\0")
            self.assertEqual([], self.messages(skill))

    def test_node_modules_is_not_a_skill_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            skill = self.make_skill(
                Path(temp),
                "Run `scripts/tool.py`.\n",
                {"scripts/tool.py": "print(1)\n"},
            )
            vendor = skill / "scripts" / "node_modules" / "fast-check"
            vendor.mkdir(parents=True)
            (vendor / "package.json").write_text('{"name":"fast-check"}\n', encoding="utf-8")
            self.assertEqual([], self.messages(skill))

    def test_unknown_slash_command_in_docs_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("Use `/ghost-skill` to start.\n", encoding="utf-8")
            messages = [finding.message for finding in AUDIT.check_docs_vs_tree(root, {"ketchup"}, set())]
            self.assertIn("names /ghost-skill, which no dstack skill provides", messages)

    def test_docs_count_claim_must_match_the_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("The mode ships 18 playbooks.\n", encoding="utf-8")
            messages = [
                finding.message
                for finding in AUDIT.check_docs_vs_tree(root, {"ketchup"}, {"babysit"})
            ]
            self.assertTrue(any("ships 18 playbooks" in message for message in messages))

    def test_docs_anchor_must_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("# Title\n\nSee [later](./guide.md#missing).\n", encoding="utf-8")
            (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "skills" / "dstack-help").mkdir(parents=True)
            (root / "skills" / "dstack-help" / "page.md").write_text(
                "See [later](../../guide.md#missing).\n",
                encoding="utf-8",
            )
            messages = [finding.message for finding in AUDIT.check_docs_vs_tree(root, set(), set())]
            self.assertTrue(any("has no heading with that anchor" in message for message in messages))

    def make_sync_root(self, root: Path, sync_text: str) -> Path:
        (root / "skills" / "how").mkdir(parents=True)
        (root / "PSTACK_SYNC.md").write_text(sync_text, encoding="utf-8")
        return root

    def sync_text(self, playbooks=None, skills=("figure-it-out",)):
        playbooks = sorted(AUDIT.EXCLUDED_DSTACK_PLAYBOOKS if playbooks is None else playbooks)
        return (
            "Pinned: pstack 1.0.0, commit `{}`.\n\n".format("a" * 40)
            + "Upstream: repository `cursor/plugins`, subpath `pstack/`.\n\n## Excluded skills\n\n"
            + "".join("- `{}`: out.\n".format(name) for name in skills)
            + "\n## Excluded playbooks\n\n"
            + "".join("- `{}`: out.\n".format(name) for name in playbooks)
        )

    def test_sync_file_contract_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_sync_root(Path(temp), self.sync_text())
            self.assertEqual([], AUDIT.check_sync_file(root))

    def test_sync_file_must_match_audit_and_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_sync_root(Path(temp), self.sync_text(playbooks={"eval"}, skills=("how",)))
            (root / "KNOWN_ISSUES.md").write_text("old\n", encoding="utf-8")
            messages = [finding.message for finding in AUDIT.check_sync_file(root)]
            self.assertIn("excluded playbooks disagree with the audit", messages)
            self.assertIn("excluded pstack skill must stay absent", messages)
            self.assertTrue(any(message.startswith("retired document must stay absent") for message in messages))

    def test_missing_sync_file_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "skills").mkdir()
            messages = [finding.message for finding in AUDIT.check_sync_file(Path(temp))]
            self.assertEqual(["missing pstack sync contract"], messages)

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
