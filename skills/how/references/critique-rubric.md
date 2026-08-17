# Architectural critique rubric

Use only the lenses relevant to the subsystem.

## Abstraction fit

- Does each abstraction represent a real concept and earn its indirection?
- Do boundaries separate things that change independently?
- Is business logic separated from framework wiring where that improves tests
  or evolution?
- Would a flatter design preserve the same behavior more clearly?

## Data model

- Do structures fit actual access and mutation patterns?
- Does code repeatedly reshape data because the model fights its consumers?
- Do static types match runtime states and boundary inputs honestly?

## Boundary discipline

- Is validation concentrated at entry points?
- Do errors cross layers cleanly without repetitive wrapping or lost context?
- Are cross-boundary shapes explicit and testable?
- Can the subsystem be exercised without booting unrelated infrastructure?

## Evolution readiness

- How much would the most plausible next requirement disturb?
- Which hard-coded assumptions would need to change?
- Are compatibility paths still used, or merely preserved?

Judge plausible evolution, not imaginary extensibility.

## Complexity versus value

- Is complexity concentrated around real invariants?
- Which components are vestigial, duplicated, or speculative?
- Is there a simpler design with the same operational behavior?

## Consistency

- Does this area follow established repository patterns for similar problems?
- If it differs, does the domain justify the difference?
- Does unexplained inconsistency increase reader or maintenance cost?
