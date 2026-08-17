# Generic adapter instructions

Use this adapter when host identity is ambiguous or when the visible tool
surface does not match a named adapter.

The baseline mapping is parent-only: search and read for `explore`, edit for
`implement`, apply an explicit second-pass rubric for `review`, ask in ordinary
conversation for `ask_user`, and run available local commands for `verify`.
Parallel and agent lifecycle capabilities are unavailable, model roles inherit
the parent, isolation is advisory, and session-history, transcript, and wake
capabilities are unavailable.

If the host exposes a clearly documented generic helper facility, the lead may
upgrade only the lifecycle operations it can confirm. Use bounded task packets,
submit independent slices together only when concurrency is documented, and
keep write scopes disjoint. If a helper call fails, finish the remaining work on
the parent and state that the fan-out collapsed.

Never guess a named provider or copy its parameters based on similar-looking
tools.
