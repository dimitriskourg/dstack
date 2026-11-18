#!/usr/bin/env python3

import contextlib
import importlib.util
import io
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
- `autopilot-full`: out.

## Excluded files

- `poteto-mode/scripts/*`: tooling.

## Owned by dstack

- `setup-pstack`: replaced.

## Not imported

## Kept dstack wording

## Allowed drift

- `skills/dstack-help/references/guide/06-supported-scope.md`
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
            "pstack/skills/poteto-help/SKILL.md": "---\nname: poteto-help\ndescription: Help.\n---\n\nHelp.\n",
            "pstack/docs/guide/01-setup.md": "# Setup\n\n" + BODY,
            "pstack/docs/guide/02-poteto-mode.md": "# Mode\n\n" + BODY,
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
            "skills/dstack-help/SKILL.md": "---\nname: dstack-help\ndescription: Help.\n---\n\nHelp.\n",
            "skills/dstack-help/references/guide/01-setup.md": "# Setup\n\n" + BODY,
            "skills/dstack-help/references/guide/02-dstack-mode.md": "# Mode\n\n" + BODY,
            "skills/dstack-help/references/guide/06-supported-scope.md": "# Scope\n",
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

    def test_decided_refuses_the_pin_until_listed_or_matched(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 3.", "Line three.")})
        report = self.run_sync(target, decided=True)
        self.assertEqual(1, len(report.decisions))
        self.assertTrue(report.refused_pin)
        self.assertIn("--decided refused", report.pin_note)
        self.assertEqual(self.local["skills/how/SKILL.md"], self.read("skills/how/SKILL.md"))
        self.assertEqual(self.pinned, self.pin())
        self.assertEqual(1, self.main(target, "--decided"))

    def test_decided_moves_the_pin_when_the_file_is_listed(self):
        target = self.upstream_change({"pstack/skills/how/SKILL.md": HOW.replace("Line 3.", "Line three.")})
        sync_text = self.read("PSTACK_SYNC.md")
        (self.dstack / "PSTACK_SYNC.md").write_text(
            sync_text.replace("## Kept dstack wording\n", "## Kept dstack wording\n\n- `skills/how/SKILL.md`: keep the dstack edit.\n"),
            encoding="utf-8",
        )
        report = self.run_sync(target, decided=True)
        self.assertEqual(["skills/how/SKILL.md"], self.decision_paths(report))
        self.assertFalse(report.refused_pin)
        self.assertEqual(self.local["skills/how/SKILL.md"], self.read("skills/how/SKILL.md"))
        self.assertEqual(target, self.pin())
        self.assertIn("## Decided by hand\n\n- `skills/how/SKILL.md`", report.render())

    def test_decided_moves_the_pin_when_a_new_file_was_copied_by_hand(self):
        target = self.upstream_change({"pstack/skills/how/references/new.md": "new file\n"})
        dest = self.dstack / "skills/how/references/new.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("new file\n", encoding="utf-8")
        report = self.run_sync(target, decided=True)
        self.assertTrue(any("not copied automatically" in reason for _, reason in report.decisions))
        self.assertFalse(report.refused_pin)
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
        self.assertEqual({"setup-pstack"}, config.owned)
        self.assertEqual(("cursor/plugins", "pstack/"), (config.repository, config.subpath))
        self.assertIn("skills/dstack-mode/worker.md", (SYNC.ROOT / "PSTACK_SYNC.md").read_text(encoding="utf-8"))

    def test_new_file_in_a_kept_skill_is_not_copied(self):
        target = self.upstream_change({"pstack/skills/how/references/new.md": "new file\n"})
        report = self.run_sync(target)
        self.assertTrue(any("not copied automatically" in reason for _, reason in report.decisions))
        self.assertTrue(any("no unauthorized push" in reason for _, reason in report.decisions))
        self.assertFalse((self.dstack / "skills/how/references/new.md").exists())
        self.assertEqual(self.pinned, self.pin())

    def test_guide_page_change_applies_like_a_kept_skill(self):
        target = self.upstream_change({
            "pstack/docs/guide/01-setup.md": "# Setup\n\n" + BODY.replace("Line 9.", "Line nine."),
        })
        report = self.run_sync(target)
        self.assertEqual([], report.decisions)
        self.assertEqual(
            ["skills/dstack-help/references/guide/01-setup.md <- docs/guide/01-setup.md"],
            [path for path, _ in report.applied],
        )
        self.assertIn("Line nine.", self.read("skills/dstack-help/references/guide/01-setup.md"))
        self.assertEqual(target, self.pin())

    def test_new_guide_page_is_not_copied(self):
        target = self.upstream_change({"pstack/docs/guide/11-new.md": "# New\n"})
        report = self.run_sync(target)
        self.assertTrue(any("not copied automatically" in reason for _, reason in report.decisions))
        self.assertFalse((self.dstack / "skills/dstack-help/references/guide/11-new.md").exists())
        self.assertEqual(self.pinned, self.pin())

    def test_hyphenated_excluded_playbook_name_needs_decision(self):
        target = self.upstream_change({
            "pstack/skills/how/SKILL.md": HOW.replace("Line 9.", "See **Autopilot-full**."),
        })
        report = self.run_sync(target)
        self.assertIn("names an excluded skill or playbook", report.decisions[0][1])

    def run_drift(self):
        return SYNC.drift(self.dstack, pstack_dir=self.upstream)

    def test_drift_fails_on_an_unlisted_difference(self):
        report = self.run_drift()
        unexplained = [path for path, _ in report.unexplained]
        self.assertIn("skills/how/SKILL.md", unexplained)
        self.assertEqual(1, self.main("--drift"))

    def test_drift_passes_when_the_difference_is_listed(self):
        sync_text = self.read("PSTACK_SYNC.md")
        (self.dstack / "PSTACK_SYNC.md").write_text(
            sync_text.replace(
                "## Allowed drift\n",
                "## Allowed drift\n\n- `skills/how/SKILL.md`\n",
            ),
            encoding="utf-8",
        )
        report = self.run_drift()
        self.assertEqual([], report.unexplained)
        self.assertIn("skills/how/SKILL.md", [path for path, _ in report.listed])
        self.assertEqual(0, self.main("--drift"))

    def test_drift_maps_guide_pages(self):
        (self.dstack / "skills/dstack-help/references/guide/01-setup.md").write_text(
            "# Setup\n\nLocal overlay.\n", encoding="utf-8")
        report = self.run_drift()
        unexplained = [path for path, _ in report.unexplained]
        self.assertIn("skills/dstack-help/references/guide/01-setup.md", unexplained)

    def test_repository_drift_is_listed(self):
        report = SYNC.drift(SYNC.ROOT)
        self.assertEqual([], report.unexplained, report.render())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, SYNC.main(["--drift"]))


if __name__ == "__main__":
    unittest.main()
