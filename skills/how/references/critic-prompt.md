# Architectural critic prompt template

---

Review the architecture of a codebase subsystem. Do not edit files or mutate
external systems. Use the explanation as a map, then read the referenced code
and form an independent judgment.

## Architectural explanation

{EXPLANATION}

## Relevant files and symbols

{FILE_POINTERS}

## Critique rubric

{CRITIQUE_RUBRIC}

## Instructions

Find architectural problems, not line-level bugs or style preferences. For each
finding provide:

1. **Severity:** `structural`, `concern`, or `observation`.
2. **Finding:** the exact boundary, model, or coupling at issue.
3. **Evidence:** concrete code and dependency references.
4. **Impact:** the practical cost to correctness, testing, operation, or change.

Do not recommend a rewrite without demonstrating a current problem. Do not ask
for more abstraction without showing what it solves. An empty critique is a
valid result when the architecture fits its requirements.

