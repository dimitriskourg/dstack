### Bug fix

**You own this task. Plan, review, verify.** Delegate investigation and the fix to subagents, stay in the lead.

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix; it does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more. Same discipline for Perf, where the evidence is the trace.

1. Reproduce it yourself on the matching surface. For a CLI or TUI, Call the Skill tool with `control-cli`. For a browser, IDE, or Electron surface, Call the Skill tool with `control-ui`. Do not hand the repro to the user. Ask only with a specific reason the available control surface cannot reach the target, and only after driving it as far as it goes. A bug you cannot reproduce cannot be proven fixed.
2. Binary-search the cause. Form the candidate hypotheses, then rule them out until one survives. Call the Skill tool with `how`. Apply it to the affected subsystem. Call the Skill tool with `why`. Apply it to regression history. Each pass, take the split that cuts the most remaining problem space, get runtime evidence, eliminate. When program state is unclear, add instrumentation or logging and read it as the code runs. Don't guess. Confirm the surviving *mechanism* with runtime evidence before the step-3 architect/interrogate fan-out; a design grounded on a plausible-but-unconfirmed cause can be unanimously wrong while the real cause sits one subsystem over.
3. Plan the fix. If it crosses a function boundary, Call the Skill tool with `architect`. Delegate implementation to one subagent using your configured `bug-worker` role with a specific scope; review the diff. Repository writers are serialized.
4. Verify on the same surface; the original repro now passes. "Inconclusive" or wrong-surface is not a pass; flag it. Unit tests show branch behavior, not bug absence.
5. Stage the commits so the failing repro lands before the fix in git history; the diff tells the story. See the **tdd** skill for the failing-test-first cadence when the bug has a cheap local test path; skip it when the test would be expensive, integration-heavy, or unclear.
   This is the canonical **sequence-verifiable-units** principle skill, the failing test first and the fix on top.
Investigation uses `how` + `why` as nested fan-out groups. Use the host's reported available child capacity only when it exposes enough capacity for both groups and their children; otherwise conservatively run the groups one at a time. Drain each bounded wave before starting the next. Retry a denied group later, then complete its pass in the current agent if it still cannot run. Report the number of parallel waves, any serialized fallback, and any lost independence.

**Reply:** what was broken, root cause, fix, how you verified. Paste failing-then-passing repro output verbatim.
