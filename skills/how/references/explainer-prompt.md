# Explainer prompt template

Use this contract for a direct parent explanation or for a read-only synthesis
helper.

---

Write an architectural explanation for a senior engineer unfamiliar with this
area.

## Original question

> {QUESTION}

## Evidence

{EXPLORER_FINDINGS_OR_DIRECT_TRACE}

## Instructions

Reconcile overlapping evidence and resolve contradictions by reading the code.
Distinguish confirmed behavior from inference. Produce a coherent mental model,
not an annotated source listing.

Use only the sections that help:

### Overview

What the subsystem is, what it does, and why it exists.

### Key concepts

Brief definitions of the few abstractions needed to understand the flow.

### How it works

A concrete step-by-step runtime or data-flow explanation. Reference exact files
and symbols without dumping large code blocks.

Include a diagram only when it makes multi-component relationships or changing
state materially easier to understand.

### Where things live

A compact maintainer map of the important files and directories.

### Gotchas

Non-obvious behavior, historical constraints, sharp edges, and evidence gaps.

Use concrete language. Explain why complexity exists. Do not pad simple flows,
and do not conceal anything the exploration could not verify.

