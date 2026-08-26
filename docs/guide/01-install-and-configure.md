# Install and configure

Preview with `python3 install.py --dry-run`, then install with `python3 install.py`. Add `--with-claude-links` only when compatibility links under `~/.claude/skills` are wanted.

After installation, Call the Skill tool with `setup-dstack`. It identifies the active harness, reads a trustworthy model catalog when available, confirms four profiles, finds the transcript directory scoped to the active workspace, and atomically writes `DSTACK_HOME/config.json`.

The schema stays at version 2 while dstack is under development. A missing transcript directory is stored as `null`; transcript-backed workflows then use visible conversation or explicit exports.
