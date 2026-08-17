### Autonomous run

**You own the exit condition. Define done, then drive to it without stopping.** For "going to bed" / "run until done" / "long-run/loop until X".

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero). A vague goal stalls; a predicate lets you stop.
2. Use `runtime.wake` when the selected adapter exposes it. An event to watch (CI, a merge, a ref advancing) gets an event wake with a bounded heartbeat fallback. Without `runtime.wake`, continue only while the parent session is active and leave a durable handoff before stopping. Never claim persistence the host cannot provide.
3. Each iteration makes the smallest change the evidence justifies, verifies it against the predicate, commits if it advanced, discards changes that didn't help. Belt-and-suspenders that "might help" gets reverted, not left to ride.
   Sequence the work via the **sequence-verifiable-units** principle skill, verifying each unit before the next instead of batching checks at the end.
4. Mid-run discoveries are yours within the authorized task scope. Address blockers and fixable drift through dstack-mode. Keep unrelated improvements as reported follow-ups rather than silently expanding scope. Use `ask_user` only for irreversible actions, genuine product or preference calls, or a real dead end. Return to the predicate after each side fix.
5. Checkpoint every iteration via the **show-me-your-work** skill, a row for what changed and whether the predicate moved. A run with no trail can't be audited or resumed.
6. Stop when the predicate is met. A plateau is not a stop, so keep going and pivot your approach to push past it. Surface a genuine dead end rather than spinning, and never relax the predicate to declare victory.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
