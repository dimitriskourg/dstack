# Install and configure

Preview with `python3 install.py --dry-run`, then install with `python3 install.py`. Add `--with-claude-links` only when compatibility links under `~/.claude/skills` are wanted.

After installation, explicitly invoke `setup-dstack`. It identifies the active harness, reads a trustworthy model catalog when available, confirms four profiles, finds the transcript directory scoped to the active workspace, and atomically writes the fixed file `~/.dstack/config.json`.

The path and host selection cannot be overridden. A config-dependent skill uses the lowercase active harness id and stops when the file is missing or invalid, the harness cannot be identified, or the required host/profile entry is unavailable.

Each profile must name a concrete model and effort pair exposed by that harness. Setup does not offer parent inheritance or automatic model selection as profile values. Take effort values from the harness's own enumeration: a harness can accept an unknown effort silently and then run the worker at the session effort.

Setup also records how the harness binds a worker to a pair, in the host entry's `worker_binding`:

- `spawn-arguments`: the spawn call carries both the model and the effort, and `definitions_directory` is `null`.
- `worker-definitions`: the spawn call cannot carry both, so setup writes one generated worker definition per profile into the harness's own definitions directory.

For a `worker-definitions` harness, setup runs `worker_bindings.py --host <active-host>`. The command synchronizes and confirms the four generated definitions and leaves every other file in that directory alone. A failure is a failed setup.

The schema stays at version 2 while dstack is under development. A missing transcript directory is stored as `null`; transcript-backed workflows then use visible conversation or explicit exports.
