# Explorer prompt template

Fill in the placeholders and send this packet to a read-only helper, or work
through it yourself when helpers are unavailable.

---

You are tracing how part of a codebase works. Do not edit files or mutate any
external system. Gather facts from implementations and artifacts; a separate
synthesis step will write the human-facing explanation.

## Question

> {QUESTION}

## Exploration angle

{EXPLORATION_ANGLE}

## Instructions

1. Find the entry point or trigger.
2. Follow callers, callees, types, and data transformations from input to
   output or trigger to effect.
3. Map the central abstractions and why each boundary exists.
4. Identify inputs, outputs, persistence, external systems, and failure paths.
5. Read the implementation; do not infer behavior from file names.
6. Stop only when you can describe the assigned path without hand-waving. Mark
   every unresolved connection explicitly.

## Return

### Components found

For each central component: symbol, file path, and responsibility.

### Flow

Numbered execution steps with functions, files, calls, and data shapes.

### Files read

Every file used as evidence.

### Boundaries

Inputs, outputs, and connections to other subsystems.

### Non-obvious behavior

Surprises, hidden state, ordering rules, or likely newcomer mistakes.

### Open questions

Anything not verified. Never fill a gap by guessing.

