# Install and configure

Preview with `python3 install.py --dry-run`, then install with `python3 install.py`. Add `--with-claude-links` only when compatibility links under `~/.claude/skills` are wanted.

After installation, Call the Skill tool with `setup-dstack`. It identifies the active harness, reads a trustworthy model catalog when available, confirms four profiles, finds the transcript directory scoped to the active workspace, and atomically writes the fixed file `~/.dstack/config.json`.

The path and host selection cannot be overridden. A config-dependent skill uses the lowercase active harness id and stops when the file is missing or invalid, the harness cannot be identified, or the required host/profile entry is unavailable.

Each profile must name a concrete model and effort pair exposed by that harness. Setup does not offer parent inheritance or automatic model selection as profile values.

The schema stays at version 2 while dstack is under development. A missing transcript directory is stored as `null`; transcript-backed workflows then use visible conversation or explicit exports.
