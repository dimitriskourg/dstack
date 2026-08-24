# Cursor adapter instructions

## Detection

Select this adapter only when Cursor system identity and its visible helper
tooling agree. Otherwise select `generic`.

## Mapping

- Map `agents.spawn` to Cursor's current helper task operation. Choose a
  read-oriented helper when available; otherwise forbid all writes in the task
  packet.
- Use the host's current result, wait, follow-up, and stop operations for the
  matching lifecycle capabilities. Do not assume a parameter from an older
  Cursor build exists in the current one.
- Map `parallel` to independent helper calls submitted together or supported
  background execution. Keep write scopes disjoint.
- Map `review` to separate read-only tasks with explicit rubrics.
- Supply a model identifier only from a confirmed local catalog or explicit
  user binding. Omit it for `inherit-parent`.
- Do not map a configured effort unless the current Cursor operation explicitly
  exposes an effort parameter and accepted values. Otherwise effort inherits
  from the parent; static dstack files do not prove Cursor effort support.

Read-only prompts are advisory unless the active helper facility explicitly
enforces permissions. The lead owns synthesis, final judgment, diff inspection,
and verification. A denied or absent helper operation falls back to the parent
without borrowing another provider's call schema.

Use `runtime.wake` only through the current documented long-running mechanism.
Treat conversation history as unavailable unless a first-class scoped resource
is visible. Transcripts for the active workspace may be readable on disk; read
only that workspace's directory and never another's.
