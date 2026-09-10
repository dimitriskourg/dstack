# Install and configure

Preview with `python3 install.py --dry-run`, then install with `python3 install.py` for Codex and Cursor. For Claude Code, install with `python3 install.py --with-claude-links`; local Claude Code discovers the managed skills through `~/.claude/skills`.

After installation, explicitly invoke `setup-dstack`. It maps the system-provided product identity to `codex`, `claude`, or `cursor`, reads a trustworthy model catalog when available, confirms four profiles, derives the canonical Git repository root, finds that repository's transcript directory, and atomically writes the fixed file `~/.dstack/config.json`.

The path and host selection cannot be overridden. Aliases such as `claude-code` are invalid. A transcript-backed skill selects `hosts[<active-harness>].repositories[<canonical-repository-root>]` when that key is the current checkout, or the registered checkout that shares `git rev-parse --git-common-dir`, then verifies the repeated `repository_root`. It does not fall back to a different Git repository. Config-dependent skills stop when the file is missing or invalid, an identity cannot be derived, or a required entry is unavailable.

Each profile must name a concrete model and effort pair exposed by that harness. Setup does not offer parent inheritance or automatic model selection as profile values. Take effort values from the harness's own enumeration: a harness can accept an unknown effort silently and then run the worker at the session effort.

A spawn list that fuses model and effort into one identifier, or that only lists the models and efforts currently selected in the host picker, is a partial catalog. Setup still stores a separate model and effort. It does not treat that session list as complete, and it does not mark an existing pair invalid only because this session cannot pass it as a spawn argument.

Setup also records how the harness binds a worker to a pair, in the host entry's `worker_binding`:

- `spawn-arguments`: the spawn call carries both the model and the effort, `definitions_directory` is `null`, and `pair_encoding` is `null`.
- `worker-definitions`: the spawn call cannot carry both, so setup writes one generated worker definition per profile into the harness's own definitions directory. `pair_encoding` is `sibling-fields` when those files have separate model and effort fields, or `model-brackets` when the model field accepts `id[effort=value]`.

For a `worker-definitions` harness, setup runs `worker_bindings.py --host <active-host>`. The command synchronizes and confirms the four generated definitions in the recorded encoding and leaves every other file in that directory alone. A failure is a failed setup.

The schema stays at version 2 while dstack is under development. A missing transcript directory is stored as `null`; transcript-backed workflows then use visible conversation or explicit exports.

## Uninstall

Run `python3 uninstall.py --skills-only` to remove the canonical dstack skills and their Claude compatibility links while preserving configuration. Run `python3 uninstall.py --all` to also remove generated dstack worker definitions and the complete `~/.dstack` directory. Either mode accepts `--dry-run` for a non-mutating preview. The uninstaller fails before removals when ownership of any discovered dstack artifact cannot be verified, and it does not remove unrelated skills or worker definitions.
