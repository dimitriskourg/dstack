# Choose focused workflows

Use `dstack-mode` by default. Invoke a focused skill directly when you need its
specific product rather than the whole mode.

## Understand before editing

### `how`

Trace current architecture, runtime flow, state ownership, or placement:

```text
how does an authenticated request reach this database command?
```

### `why`

Investigate historical motivation using code, commits, discussions, and other
authorized evidence:

```text
why was this queue introduced instead of writing synchronously?
```

### `teach`

Combine current mechanics and historical rationale into an explanation aimed at
a specific reader.

### `recall`

Reconstruct prior work from your recent chats in this workspace, explicit
handoffs, and repository state. It reads only this workspace's transcripts, and
says so when none are readable.

## Design before committing

### `architect`

Produce a concrete implementation architecture with ownership boundaries,
interfaces, sequencing, and verification.

### `arena`

Generate genuinely different candidates and cross-judge them. It is useful for
one-way design decisions or changes with several credible shapes.

### `interrogate`

Stress-test a plan with several skeptical reviewers at once, on distinct models
where your configuration provides them. The lead owns the final synthesis rather
than counting votes.

### `swarm`

Fan out independent artifacts or investigations. Do not use it to let several
writers edit the same state concurrently.

## Build and clean

### `tdd`

Pin behavior, reproduce the missing case, implement the smallest fix, and keep
the test meaningful.

### `unslop`

Remove vague, repetitive, inflated, or mechanically generated prose without
changing the underlying meaning.

### `no-comments` and `comment-sicko`

Review comments for reader value. Remove narration and stale implementation
restatements; retain constraints, non-obvious invariants, and externally imposed
behavior.

## Verify and explain confidence

### `create-verification-skill`

Create a reusable agent-facing procedure for launching, driving, proving, and
cleaning up a real application. Personal output defaults to
`~/.agents/skills/verify-<app>`; project-local output requires an explicit
choice.

### `maintain-verification-skill`

Audit a verification skill against current source and a live pass. Do not edit
product code to hide a product failure.

### `blast-radius`

Find what a change could break and prove the load-bearing safety claim with
real evidence.

### `show-me-your-work`

Keep a compact decision trail for meaningful forks, reversals, blockers, and
verified iterations. Do not log every shell command.

## Generate or evolve personal workflows

### `automate-me`

Create or revise a personal mode skill from explicit preferences and authorized
evidence. It defaults to `~/.agents/skills` and does not create provider-specific
compatibility copies.

### `reflect`

Extract reusable lessons from the current work while disclosing any missing
history or independent-review capability.

Next: [Maintain dstack and sync pstack](./05-maintaining-dstack.md).
