#!/usr/bin/env python3

import contextlib
import base64
import hashlib
import html
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pstack_sync.py"
SPEC = importlib.util.spec_from_file_location("pstack_sync", SCRIPT)
assert SPEC and SPEC.loader
SYNC = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SYNC
SPEC.loader.exec_module(SYNC)

BODY = "".join("Line {}.\n".format(number) for number in range(1, 11))
HOW = "---\nname: how\ndescription: Explain code.\ndisable-model-invocation: true\n---\n\n" + BODY
MODE = "---\nname: poteto-mode\ndescription: The poteto agent style.\n---\n\nRead the poteto-mode playbooks.\n\n" + BODY
SYNC_DOC = """# pstack sync

Pinned: pstack 1.0.0, commit `{commit}`.

Upstream: repository `cursor/plugins`, subpath `pstack/`.

## Excluded skills

- `figure-it-out`: out.

## Excluded playbooks

- `eval`: out.

## Excluded files

- `poteto-mode/scripts/*`: tooling.

## Owned by dstack

- `setup-pstack`: replaced.
"""


class PstackSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.upstream = root / "plugins"
        self.dstack = root / "dstack"
        self.write_upstream({
            "pstack/plugin.json": '{"name": "pstack", "version": "1.0.0"}\n',
            "pstack/README.md": "pstack\n",
            "pstack/skills/how/SKILL.md": HOW,
            "pstack/skills/poteto-mode/SKILL.md": MODE,
            "pstack/skills/poteto-mode/playbooks/bug-fix.md": "# Bug fix\n\n" + BODY,
            "pstack/skills/poteto-mode/playbooks/eval.md": "# Eval\n\n" + BODY,
            "pstack/skills/figure-it-out/SKILL.md": "---\nname: figure-it-out\ndescription: x\n---\n\n" + BODY,
            "pstack/skills/setup-pstack/SKILL.md": "---\nname: setup-pstack\ndescription: x\n---\n\n" + BODY,
        })
        self.cache = root / "cache"
        self.git("init", "-q", "-b", "main")
        self.git("config", "uploadpack.allowAnySHA1InWant", "true")
        self.pinned = self.commit("pinned")
        self.local = {
            "skills/how/SKILL.md": HOW.replace("disable-model-invocation: true\n", "").replace(
                "Line 2.", "Line 2, edited by dstack."),
            "skills/dstack-mode/SKILL.md": SYNC.rewrite_names(MODE),
            "skills/dstack-mode/playbooks/bug-fix.md": "# Bug fix\n\n" + BODY,
            "skills/setup-dstack/SKILL.md": "---\nname: setup-dstack\ndescription: x\n---\n\nOwn text.\n",
        }
        for path, text in self.local.items():
            target = self.dstack / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        (self.dstack / "PSTACK_SYNC.md").write_text(SYNC_DOC.format(commit=self.pinned), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
             "-c", "core.fsmonitor=false", "-C", str(self.upstream), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def write_upstream(self, files):
        for path, text in files.items():
            target = self.upstream / path
            if text is None:
                target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def upstream_change(self, files):
        self.write_upstream(files)
        return self.commit("target")

    def run_sync(self, target, **options):
        return SYNC.sync(target, self.dstack, repo_url=self.upstream.as_uri(), cache_dir=self.cache, **options)

    def run_alignment(self, target=None, **options):
        return SYNC.check_alignment(target, self.dstack, repo_url=self.upstream.as_uri(), cache_dir=self.cache, **options)

    def main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return SYNC.main([
                *args, "--repo-url", self.upstream.as_uri(), "--cache-dir", str(self.cache),
                "--dstack-root", str(self.dstack),
            ])

    def read(self, path):
        return (self.dstack / path).read_text(encoding="utf-8")

    def pin(self):
        return SYNC.parse_sync(self.read("PSTACK_SYNC.md")).commit

    def decision_paths(self, report):
        return [path for path, _ in report.decisions]

    def test_pinned_target_is_a_no_op(self):
        report = self.run_sync(self.pinned, dry_run=True)
        self.assertEqual(([], [], []), (report.applied, report.skipped, report.decisions))
        self.assertIn("Result: no-op", report.render())
        self.assertEqual(self.main(self.pinned, "--dry-run"), 0)

    def test_clean_change_applies_with_rewrites_and_moves_the_pin(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line 9, now pointing at poteto-mode."),
            "pstack/README.md": "pstack 2\n",
        })
        report = self.run_sync(target)
        self.assertEqual([], report.decisions)
        self.assertEqual(["skills/how/SKILL.md"], [path for path, _ in report.applied])
        text = self.read("skills/how/SKILL.md")
        self.assertIn("Line 9, now pointing at dstack-mode.", text)
        self.assertIn("Line 2, edited by dstack.", text)
        self.assertNotIn("disable-model-invocation", text)
        self.assertEqual(target, self.pin())

    def test_dry_run_writes_nothing(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line nine.")})
        report = self.run_sync(target, dry_run=True)
        self.assertEqual(1, len(report.applied))
        self.assertEqual(self.local["skills/how/SKILL.md"], self.read("skills/how/SKILL.md"))
        self.assertEqual(self.pinned, self.pin())

    def test_change_next_to_dstack_edit_needs_decision_and_keeps_pin(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 3.", "Line three.")})
        report = self.run_sync(target)
        self.assertEqual(["skills/how/SKILL.md"], self.decision_paths(report))
        self.assertIn("next to lines dstack changed", report.decisions[0][1])
        self.assertEqual(self.local["skills/how/SKILL.md"], self.read("skills/how/SKILL.md"))
        self.assertEqual(self.pinned, self.pin())
        self.assertEqual(1, self.main(target))
        text = report.render()
        self.assertIn("## Needs decision", text)
        self.assertIn("  pstack change:\n\n  ```diff\n", text)
        self.assertIn("  -Line 3.\n  +Line three.\n", text)
        self.assertIn("  dstack lines it clashes with:\n\n  ```text\n", text)
        self.assertIn("  Line 2, edited by dstack.\n", text)

    def test_detail_fence_outlasts_fences_in_the_skill(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 3.", "```\nLine 3.\n```")})
        text = self.run_sync(target, dry_run=True).render()
        self.assertIn("  ````diff\n", text)

    def test_decided_moves_the_pin_without_writing(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 3.", "Line three.")})
        report = self.run_sync(target, decided=True)
        self.assertEqual(1, len(report.decisions))
        text = report.render()
        self.assertIn("## Decided by hand\n\n- `skills/how/SKILL.md`", text)
        self.assertIn("1 decided by hand", text)
        self.assertNotIn("Needs decision", text)
        self.assertEqual(self.local["skills/how/SKILL.md"], self.read("skills/how/SKILL.md"))
        self.assertEqual(target, self.pin())

    def test_new_skill_and_new_playbook_are_not_imported(self):
        target = self.upstream_change({
            "pstack/skills/brand-new/SKILL.md": "---\nname: brand-new\ndescription: x\n---\n",
            "pstack/skills/brand-new/references/a.md": "a\n",
            "pstack/skills/poteto-mode/playbooks/new-flow.md": "# New flow\n",
        })
        report = self.run_sync(target)
        self.assertEqual(
            ["skills/brand-new", "skills/poteto-mode/playbooks/new-flow.md"], sorted(self.decision_paths(report)))
        self.assertFalse((self.dstack / "skills/brand-new").exists())
        self.assertFalse((self.dstack / "skills/dstack-mode/playbooks/new-flow.md").exists())

    def test_spawn_and_model_wording_needs_decision(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Spawn explorers on the fast model."),
        })
        report = self.run_sync(target)
        self.assertIn("spawn, model, effort, or config wording", report.decisions[0][1])

    def test_host_specific_path_needs_decision(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Read ~/.cursor/rules/notes.md."),
        })
        report = self.run_sync(target)
        self.assertIn("host-specific", report.decisions[0][1])

    def test_new_frontmatter_key_needs_decision_but_cursor_only_keys_are_stripped(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("description:", "paths:\n  - '**/*.ts'\nmetadata: x\ndescription:"),
        })
        report = self.run_sync(target)
        self.assertIn("new frontmatter key(s): metadata", report.decisions[0][1])
        self.assertNotIn("paths", report.decisions[0][1])

    def test_description_change_next_to_kept_dstack_frontmatter_applies(self):
        local = self.local["skills/how/SKILL.md"].replace(
            "description: Explain code.\n", "description: Explain code.\ndisable-model-invocation: true\n")
        (self.dstack / "skills/how/SKILL.md").write_text(local, encoding="utf-8")
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Explain code.", "Explain any code.")})
        report = self.run_sync(target)
        self.assertEqual([], report.decisions)
        self.assertEqual(local.replace("Explain code.", "Explain any code."), self.read("skills/how/SKILL.md"))

    def test_skill_directive_becomes_the_exact_phrase(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line 9. Run the **poteto-mode** skill."),
        })
        report = self.run_sync(target)
        self.assertEqual([], report.decisions)
        self.assertIn("Line 9. Call the Skill tool with `dstack-mode`.", self.read("skills/how/SKILL.md"))

    def test_excluded_change_is_skipped_unless_it_names_a_kept_skill(self):
        target = self.upstream_change({
            "pstack/skills/figure-it-out/SKILL.md": "---\nname: figure-it-out\ndescription: x\n---\n\nNew text.\n",
            "pstack/skills/poteto-mode/scripts/tool.ts": "export {}\n",
            "pstack/skills/poteto-mode/playbooks/eval.md": "# Eval\n\nThen use the **how** skill.\n",
        })
        report = self.run_sync(target)
        self.assertEqual(["skills/poteto-mode/playbooks/eval.md"], self.decision_paths(report))
        skipped = [path for path, _ in report.skipped]
        self.assertIn("skills/figure-it-out/SKILL.md", skipped)
        self.assertIn("skills/poteto-mode/scripts/tool.ts", skipped)

    def test_kept_file_naming_an_excluded_skill_needs_decision(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line 9, see **figure-it-out**."),
        })
        report = self.run_sync(target)
        self.assertIn("names an excluded skill or playbook", report.decisions[0][1])

    def test_kept_skill_deleted_upstream_needs_decision(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": None})
        report = self.run_sync(target)
        self.assertEqual(["skills/how/SKILL.md"], self.decision_paths(report))
        self.assertIn("kept skill renamed or deleted upstream", report.decisions[0][1])
        self.assertTrue((self.dstack / "skills/how/SKILL.md").is_file())

    def test_owned_skill_change_needs_decision(self):
        target = self.upstream_change({
            "pstack/skills/setup-pstack/SKILL.md": "---\nname: setup-pstack\ndescription: x\n---\n\nChanged.\n",
        })
        report = self.run_sync(target)
        self.assertEqual(["skills/setup-pstack/SKILL.md"], self.decision_paths(report))
        self.assertIn("Own text.", self.read("skills/setup-dstack/SKILL.md"))

    def test_losing_the_config_call_line_needs_decision(self):
        local = self.local["skills/how/SKILL.md"].replace(
            "Line 6.", "Line 6. Call the Skill tool with `dstack-config`.")
        (self.dstack / "skills/how/SKILL.md").write_text(local, encoding="utf-8")
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 6.\n", "")})
        report = self.run_sync(target)
        self.assertEqual(["skills/how/SKILL.md"], self.decision_paths(report))

    def test_rerun_after_apply_reports_already_in_dstack(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line nine.")})
        self.run_sync(target)
        (self.dstack / "PSTACK_SYNC.md").write_text(SYNC_DOC.format(commit=self.pinned), encoding="utf-8")
        report = self.run_sync(target)
        self.assertEqual([("skills/how/SKILL.md", "already in dstack")], report.skipped)

    def test_default_target_is_the_latest_main(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line nine.")})
        report = SYNC.sync(dstack_root=self.dstack, repo_url=self.upstream.as_uri(), cache_dir=self.cache, dry_run=True)
        self.assertEqual(target, report.target)
        self.assertIn("Write run: python3 scripts/pstack_sync.py " + target, report.render())
        self.assertEqual(self.pinned, self.pin())

    def test_write_run_requires_a_full_target_commit(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line nine.")})
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.main()
        for ref in ("main", target[:7]):
            with self.assertRaises(SystemExit) as raised:
                self.run_sync(ref)
            self.assertIn("explicit full target commit", str(raised.exception.code))
        self.assertEqual(self.local["skills/how/SKILL.md"], self.read("skills/how/SKILL.md"))
        self.assertEqual(self.pinned, self.pin())
        self.assertEqual(0, self.main(target))

    def test_tag_target_and_shallow_cache(self):
        self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line nine.")})
        self.git("tag", "v2")
        tagged = self.git("rev-parse", "v2")
        self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line 9, later.")})
        report = self.run_sync("v2", dry_run=True)
        self.assertEqual(tagged, report.target)
        caches = list(self.cache.iterdir())
        self.assertEqual(1, len(caches))
        self.assertTrue((caches[0] / "shallow").is_file())

    def test_local_pstack_dir_reads_without_fetching(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "Line nine.")})
        report = SYNC.sync(target, self.dstack, pstack_dir=self.upstream, dry_run=True)
        self.assertEqual(["skills/how/SKILL.md"], [path for path, _ in report.applied])
        self.assertFalse(self.cache.exists())

    def test_sync_file_must_name_the_upstream_repository(self):
        with self.assertRaises(SystemExit):
            SYNC.parse_sync("Pinned: pstack 1.0.0, commit `{}`.\n".format("a" * 40))

    def test_repository_sync_file_parses(self):
        config = SYNC.parse_sync((SYNC.ROOT / "PSTACK_SYNC.md").read_text(encoding="utf-8"))
        self.assertRegex(config.version, r"^\d+\.\d+\.\d+$")
        self.assertRegex(config.commit, r"^[0-9a-f]{40}$")
        self.assertIn("figure-it-out", config.excluded_skills)
        self.assertIn("shipping", config.excluded_playbooks)
        self.assertEqual({"setup-pstack", "comment-sicko", "control-ui", "deslop", "dstack-config"}, config.owned)
        self.assertEqual(("cursor/plugins", "pstack/"), (config.repository, config.subpath))

    def test_alignment_at_the_pin_reports_existing_drift_without_writing(self):
        before = {path.relative_to(self.dstack): path.read_bytes() for path in self.dstack.rglob("*") if path.is_file()}
        report = self.run_alignment()
        entries = {entry.dstack_path: entry for entry in report.files}
        self.assertEqual(self.pinned, report.target)
        self.assertEqual("different", entries["skills/how/SKILL.md"].status)
        self.assertIn("Line 2, edited by dstack.", entries["skills/how/SKILL.md"].normalized_diff)
        self.assertEqual("rewritten", entries["skills/dstack-mode/SKILL.md"].status)
        self.assertEqual("identical", entries["skills/dstack-mode/playbooks/bug-fix.md"].status)
        self.assertIn("skills/setup-dstack", report.dstack_owned)
        self.assertIn(("skills/figure-it-out", "out."), report.excluded)
        self.assertIn(("skills/poteto-mode/playbooks/eval.md", "out."), report.excluded)
        after = {path.relative_to(self.dstack): path.read_bytes() for path in self.dstack.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(0, self.main("--check-alignment"))

    def test_alignment_normalizes_both_sides_and_retains_the_raw_diff(self):
        (self.dstack / "skills/how/SKILL.md").write_text(HOW.replace("disable-model-invocation: true\n", ""), encoding="utf-8")
        report = self.run_alignment()
        entry = next(entry for entry in report.files if entry.dstack_path == "skills/how/SKILL.md")
        self.assertEqual("rewritten", entry.status)
        self.assertIn("-disable-model-invocation: true", entry.diff)
        self.assertEqual("", entry.normalized_diff)
        self.assertNotEqual(entry.upstream_sha256, entry.dstack_sha256)
        self.assertNotIn("-disable-model-invocation: true", report.render())

    def test_alignment_lists_new_skills_playbooks_and_missing_assets(self):
        target = self.upstream_change({
            "pstack/skills/README.md": "Skill packaging, not a skill\n",
            "pstack/skills/new-skill/SKILL.md": "# New skill\n",
            "pstack/skills/poteto-mode/playbooks/new-playbook.md": "# New playbook\n",
            "pstack/skills/how/references/new.md": "New reference\n",
            "pstack/skills/poteto-mode/scripts/excluded.py": "Excluded script\n",
        })
        report = self.run_alignment(target)
        self.assertEqual(["skills/new-skill", "skills/poteto-mode/playbooks/new-playbook.md"], report.not_imported)
        entry = next(entry for entry in report.files if entry.dstack_path == "skills/how/references/new.md")
        self.assertEqual("missing-local", entry.status)
        self.assertIsNone(entry.dstack_sha256)
        self.assertIn("-New reference", entry.normalized_diff)
        self.assertFalse(any(entry.dstack_path.endswith("excluded.py") for entry in report.files))
        self.assertEqual(self.pinned, self.pin())

    def test_alignment_separates_owned_sidecars_from_local_only_files(self):
        sidecar = self.dstack / "skills/how/agents/openai.yaml"
        sidecar.parent.mkdir()
        sidecar.write_text("interface: {}\n", encoding="utf-8")
        extra = self.dstack / "skills/how/extra.txt"
        extra.write_text("Local only\n", encoding="utf-8")
        local_skill = self.dstack / "skills/local-skill/SKILL.md"
        local_skill.parent.mkdir()
        local_skill.write_text("# Local skill\n", encoding="utf-8")
        report = self.run_alignment()
        self.assertIn("skills/how/agents/openai.yaml", report.dstack_owned)
        entries = {entry.dstack_path: entry for entry in report.files}
        self.assertNotIn("skills/how/agents/openai.yaml", entries)
        for name in ("skills/how/extra.txt", "skills/local-skill/SKILL.md"):
            self.assertEqual("local-only", entries[name].status)
            self.assertIsNone(entries[name].upstream_path)

    def test_alignment_handles_binary_content_and_ignores_generated_files(self):
        for name, data in (("same.bin", b"\x00\xff"), ("different.bin", b"\x00\xfe")):
            (self.upstream / "pstack/skills/how" / name).write_bytes(data)
            (self.dstack / "skills/how" / name).write_bytes(b"\x00\xff")
        target = self.commit("binary assets")
        for name in ("__pycache__/cache.pyc", "node_modules/example/index.js", ".DS_Store"):
            path = self.dstack / "skills/how" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("generated", encoding="utf-8")
        report = self.run_alignment(target)
        entries = {entry.dstack_path: entry for entry in report.files}
        self.assertEqual("identical", entries["skills/how/same.bin"].status)
        binary = entries["skills/how/different.bin"]
        self.assertEqual("different", binary.status)
        self.assertIn("Binary content", binary.diff)
        self.assertNotEqual(binary.upstream_sha256, binary.dstack_sha256)
        self.assertFalse(any("generated" in entry.diff for entry in report.files))

    def test_alignment_reports_deleted_upstream_files_as_local_only_not_owned(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": None})
        report = self.run_alignment(target)
        entry = next(entry for entry in report.files if entry.dstack_path == "skills/how/SKILL.md")
        self.assertEqual("local-only", entry.status)
        self.assertNotIn("skills/how", report.dstack_owned)

    def test_alignment_local_folder_reads_the_git_snapshot_not_uncommitted_upstream(self):
        self.write_upstream({"pstack/skills/how/SKILL.md": "Uncommitted upstream edit\n"})
        report = SYNC.check_alignment(dstack_root=self.dstack, pstack_dir=self.upstream / "pstack")
        entry = next(entry for entry in report.files if entry.dstack_path == "skills/how/SKILL.md")
        self.assertIn("Line 2.", entry.diff)
        self.assertNotIn("Uncommitted upstream edit", entry.diff)
        self.assertFalse(self.cache.exists())

    def test_alignment_preserves_missing_final_newlines_in_diffs(self):
        (self.dstack / "skills/dstack-mode/playbooks/bug-fix.md").write_text("# Bug fix", encoding="utf-8")
        report = self.run_alignment()
        entry = next(entry for entry in report.files if entry.dstack_path.endswith("bug-fix.md"))
        self.assertIn("\\ No newline at end of file", entry.diff)

    def test_alignment_json_and_markdown_are_deterministic(self):
        output = Path(self.temp.name) / "alignment.json"
        self.assertEqual(0, self.main("--check-alignment", "--format", "json", "--report", str(output)))
        first = output.read_bytes()
        payload = json.loads(first)
        self.assertEqual(self.pinned, payload["target"])
        self.assertEqual(sorted(entry["dstack_path"] for entry in payload["files"]), [entry["dstack_path"] for entry in payload["files"]])
        self.assertEqual(0, self.main("--check-alignment", "--format", "json", "--report", str(output)))
        self.assertEqual(first, output.read_bytes())
        self.assertEqual(self.run_alignment().render(), self.run_alignment().render())

    def test_alignment_rejects_write_flags_and_reports_inside_the_source_tree(self):
        for options in (("--decided",), ("--dry-run",), ("--report", str(self.dstack / "PSTACK_SYNC.md"))):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.main("--check-alignment", *options)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.main("--dry-run", "--format", "json")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.main("--check-alignment", "--pstack-dir", str(self.upstream), "--report", str(self.upstream / "pstack/plugin.json"))
        self.assertEqual(self.pinned, self.pin())

    def html_payload(self, document):
        return json.loads(re.search(r'<script id="report-data" type="application/json">(.*?)</script>', document, re.S).group(1))

    def test_html_is_deterministic_and_preserves_source_snapshots(self):
        report = self.run_alignment()
        document = report.render_html()
        self.assertEqual(document, self.run_alignment().render_html())
        payload = self.html_payload(document)
        for entry, captured in zip(report.files, payload["files"]):
            for mode, before, after in (
                ("raw", entry.upstream_text, entry.dstack_text),
                ("normalized", entry.normalized_upstream_text, entry.normalized_dstack_text),
            ):
                for side, text in (("left", before), ("right", after)):
                    index = captured[mode][side]
                    self.assertEqual(text, None if index is None else "".join(payload["sources"][index]))
        sources = ["".join(lines) for lines in payload["sources"]]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual([list(item) for item in report.excluded], payload["excluded"])
        self.assertEqual(report.dstack_owned, payload["owned"])
        self.assertEqual(report.not_imported, payload["not_imported"])

    def test_html_cli_matches_renderer_and_does_not_write_sources(self):
        output = Path(self.temp.name) / "alignment.html"
        before = {path: path.read_bytes() for path in self.dstack.rglob("*") if path.is_file()}
        self.assertEqual(0, self.main("--check-alignment", "--format", "html", "--report", str(output)))
        self.assertEqual(self.run_alignment().render_html(), output.read_text(encoding="utf-8"))
        self.assertEqual(before, {path: path.read_bytes() for path in self.dstack.rglob("*") if path.is_file()})
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.main("--dry-run", "--format", "html")

    def test_html_escapes_untrusted_data_and_hashes_inline_assets(self):
        attack = '</script><img src="https://invalid.example/" onerror="alert(1)">'
        (self.dstack / "skills/how/SKILL.md").write_text(attack, encoding="utf-8")
        report = self.run_alignment()
        report.repository = attack
        report.target_version = attack
        report.excluded.append((attack, attack))
        document = report.render_html()
        self.assertNotIn(attack, document)
        self.assertIn(html.escape(attack), document)
        payload = self.html_payload(document)
        self.assertIn([attack], payload["sources"])
        self.assertIn([attack, attack], payload["excluded"])
        for pattern in (r'<style>(.*?)</style>', r'<script>(.*?)</script>'):
            asset = re.search(pattern, document, re.S).group(1)
            digest = base64.b64encode(hashlib.sha256(asset.encode("utf-8")).digest()).decode("ascii")
            self.assertIn("sha256-" + digest, document)
        self.assertIn("default-src &#x27;none&#x27;", document)
        self.assertNotRegex(document, r'<(?:script|link|img)\b[^>]*(?:src|href)=')

    def test_html_distinguishes_binary_empty_and_missing_sources(self):
        report = self.run_alignment()
        report.files = [
            SYNC.compare_file("skills/how/a", "skills/how/a", before, after, set())
            for before, after in ((b"\x00", b"\xff"), (b"", b""), (None, b""), (b"", None))
        ]
        payload = self.html_payload(report.render_html())
        self.assertEqual([True, False, False, False], [entry["binary"] for entry in payload["files"]])
        self.assertEqual(None, payload["files"][2]["raw"]["left"])
        self.assertEqual(None, payload["files"][3]["raw"]["right"])
        empty_index = payload["files"][1]["raw"]["left"]
        self.assertEqual([], payload["sources"][empty_index])


if __name__ == "__main__":
    unittest.main()
