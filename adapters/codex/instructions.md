# Codex adapter instructions

## Detection

Select this adapter only when the session identifies itself as Codex and the
visible multi-agent tools match that identity. A path or environment variable
alone is insufficient.

## Mapping

- Map `agents.spawn` to the current sub-agent spawn operation. Use explorer
  helpers for `explore` and explicitly prohibit repository and external writes.
- Map `agents.wait`, `agents.follow_up`, `agents.interrupt`, and
  `agents.collect` to the corresponding current lifecycle operations. Do not
  inspect hidden transcript files.
- Map `parallel` to multiple independent spawns while the lead performs only
  non-overlapping work. Respect the session concurrency limit.
- Map `review` to a separate read-only helper with an explicit rubric.
- Discover the current model catalog from the operation being invoked when its
  tool schema enumerates accepted models and efforts. This is authoritative for
  that operation.
- Otherwise, if the installed `codex debug --help` advertises `models`, run
  `python3 DSTACK_HOME/adapters/codex/discover_models.py`. It reduces
  `codex debug models` to exact model-effort pairs. If neither source exists,
  report catalog validation unavailable and do not validate bindings.
- Validate the configured model and effort as a pair. Pass both native model
  and reasoning-effort parameters only when the current operation accepts the
  pair. Omit either override whose configured value is `inherit-parent`. If a
  concrete pair is invalid, inherit the parent settings and report the
  degradation once.

The standard explorer boundary is advisory: the prompt forbids writes, but it
does not prove filesystem isolation. Use enforced isolation only when the
current runtime explicitly provides it.

Treat `session.history`, `session.transcript`, and `runtime.wake` as unavailable
unless the current Codex surface exposes a first-class scoped operation. Never
infer them from local private directories.

The lead owns decomposition, synthesis, final judgment, diff inspection, and
verification. If any lifecycle action is missing or denied, apply the fallback
in `capabilities.toml` and state the degradation once.
