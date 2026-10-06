# Set up dstack

In this page you install the skills, pick which models dstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the skills

From the dstack repository, preview the installation, then install:

```sh
python3 install.py --dry-run
python3 install.py
```

Codex, Claude Code, and Cursor use the same portable skills. For Claude Code, add `--with-claude-links` to install the compatibility links. Installation preserves unrelated skills and configuration.

## Pick your models

Run:

```text
/setup-dstack
```

[`/setup-dstack`](../../../setup-dstack/SKILL.md) detects the active harness, reads its model catalog, confirms four concrete model-and-effort profiles, and records this repository's transcript directory in `~/.dstack/config.json`.

The profiles are `fast-explorer`, `feature-worker`, `bug-worker`, and `skeptical-reviewer`. Pick cheaper models or lower efforts where the work allows it. Every pair must be supported by the active harness; `auto` and `inherit-parent` are not profile values.

Setup records how the harness applies both halves of the pair. When the spawn call cannot carry effort, setup synchronizes and verifies generated worker definitions. A model-only override would leave the worker on the session effort, so it is not enough.

Run setup in each repository. Transcript consumers select the canonical Git root, or a registered checkout sharing its Git common directory. They never fall back to another repository's transcripts. A missing configuration or required entry stops config-dependent work with an explicit setup instruction.

## Accept the verification offer, or don't

At the end of setup, `/setup-dstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/create-verification-skill`](../../../create-verification-skill/SKILL.md).

Say yes and it writes a project-local `verify-<app>` skill in the active harness’s discoverable skill directory. It teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to dstack, say yes. An agent that can check its own work keeps going until the check passes. An agent that can't hands every result back to you to check by hand. Of everything in this guide, the verification skill pays off the most.

After setup, start a new chat if the harness loads generated worker definitions only at startup.

## Keep the cost in check

dstack spends extra tokens on subagents and review panels. That's the price of the rigor. To spend fewer:

- Rerun `/setup-dstack` and pick lower efforts or cheaper models. A strong model in the main chat with cheaper, faster models in the code roles is a good split.
- Save `/dstack-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/dstack-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/dstack-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. Mode lifetime depends on the active harness. Start each new task with `/dstack-mode`, and re-read it after a compaction that drops it from context. The [mode skill](../../../dstack-mode/SKILL.md) owns that contract.

Next: [Route work through `/dstack-mode`](./02-dstack-mode.md).
