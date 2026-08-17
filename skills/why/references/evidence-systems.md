# Evidence-system playbook

Assign one investigator to each available evidence category. Discover the actual connector or local interface at runtime, inspect its read operations, and never assume a vendor or call schema.

| Category | Search focus |
| --- | --- |
| Source control and review | Commits, blame, pull requests, review threads, linked issues, release boundaries. |
| Tickets and planning | Problem statements, customer constraints, deadlines, scope changes, acceptance criteria. |
| Long-form documents | Specifications, design records, postmortems, meeting notes, rejected alternatives. |
| Team communication | Decision threads, incident rooms, review discussion, contemporaneous objections. |
| Observability | Metrics, logs, traces, monitors, incident timelines, capacity thresholds. |
| Error tracking | Error groups, affected releases, stack traces, recurrence, first and last seen. |
| Product analytics | Usage distributions, experiments, feature exposure, migrations, derived thresholds. |

For each category:

1. Confirm a read-capable source is available and authorized.
2. Search from the code anchor: symbols, change IDs, dates, error strings, feature names, and linked identifiers.
3. Read full candidate records rather than snippets.
4. Follow cross-links only within the authorized task scope.
5. Return citations, search terms, time range, positive findings, null results, contradictions, and access gaps.
6. Keep direct statements separate from timing correlation and code-shape inference.

A missing connector is unavailable evidence. An available connector with no relevant matches is a null result. Do not substitute one for the other.
