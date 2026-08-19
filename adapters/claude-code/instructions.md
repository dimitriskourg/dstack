# Claude Code adapter instructions

## Detection

Select this adapter when the session identifies itself as Claude Code and
exposes its native agent/task facility. Older and newer tool names are host
details and must not leak into portable skills.

## Mapping

- Map `agents.spawn` to the current native agent operation. Prefer a built-in
  exploration helper for `explore`; otherwise explicitly prohibit edits.
- Map the other lifecycle capabilities only when the current tool surface
  exposes them. Foreground completion may satisfy both wait and collect.
- Map `parallel` to multiple independent agent calls in one turn when supported.
- Map `review` to separate read-only agents with distinct rubrics.
- Pass a model only from a confirmed binding; omit it for `inherit-parent`.
- Do not map a configured effort unless the current Claude Code operation
  explicitly exposes an effort parameter and accepted values. Otherwise effort
  inherits from the parent; static dstack files do not prove effort support.

The common read-only boundary is advisory unless the current runtime documents
technical enforcement. The lead owns synthesis, final judgment, artifact
inspection, and verification. Missing lifecycle operations fall back to parent
execution and are disclosed.

Treat session history, transcript access, and wake behavior as unavailable
unless the current tool surface explicitly provides a scoped operation.
