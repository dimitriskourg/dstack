### Feature

**You own the design. Plan, review, verify.** Delegate implementation. Stay in the lead.

1. Call the Skill tool with `how`. Apply it to the affected subsystem.
2. Call the Skill tool with `architect`. Use it for parallel design exploration. Skipping stays as `architect skipped: <reason>`. Do not fold the design decision silently into implementation.
3. Write the throughput checkpoint as four todo items. A dimension that genuinely does not apply (single file, no fan-out) keeps its item with `n/a: <reason>` rather than being dropped:
   - **Blocking first steps.** Gates run before fan-out.
   - **Independent workstreams.** Read-only exploration and artifacts outside the repository may parallelize. Repository writes serialize.
   - **Shared mutable state.** Default to splitting read-only analysis or separate output artifacts (the **separate-before-serializing-shared-state** principle skill). Do not use branches or shared checkout paths as writer isolation.
   - **Smallest safe decomposition.** If one worker is best, name why.
4. Delegate code-writing to one subagent using the configured `feature-worker` profile with a specific scope (file paths, named data shape and its organizing structure per **principle-model-the-domain**, a state machine over scattered booleans, a table/registry over branching, a typed model over repeated shape assumptions, chosen before the delegate writes logic, and success criteria). Review its diff yourself. Keep every repository writer serialized in the active checkout. When the implementation admits multiple valid shapes (error handling, abstraction layer, test structure), Call the Skill tool with `arena`. Let its isolated proposal artifacts and cross-judge guard the pick. Mandatory: no skip-with-reason escape, and Laziness Protocol does not override it (the gain is review separation, not lines saved). Every supported harness can spawn subagents. If a nested spawn is denied, the current agent owns the diff directly. No "standing by" reply that waits on a nested agent. Comments per **Comments**. Surgical edits, re-ground against upstream-derived sources. Port shared-primitive improvements to all consumers and verify each.
5. Verify on the matching surface. "Inconclusive" or wrong-surface is not a pass. Flag it.
6. Rebase into small, ordered commits. Stack follow-ups.
   Use the **sequence-verifiable-units** principle skill, building, verifying, and committing each small unit before the next.
7. If the design is contested, Call the Skill tool with `interrogate`. Do so before handing back.

Code-coupled work (one feature, one migration) goes to a single writer with the checkpoint inline. Parent-level fan-out is for read-only slices or independent artifacts outside the repository (audits, cross-subsystem investigations, competing proposals). Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.

**Reply:** what you built, what you chose and why, the throughput checkpoint, open decisions. Tables for design alternatives.
