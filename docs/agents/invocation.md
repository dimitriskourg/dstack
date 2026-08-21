# Model-invoked vs user-invoked

Every `SKILL.md` under `skills/` is a skill. The one axis that splits them is
**invocation**: who is allowed to reach it.

- **User-invoked**: reachable only by the human typing its name. Set
  `disable-model-invocation: true` in the frontmatter and
  `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- **Model-invoked**: reachable by model or user. This is the default. Omit the
  frontmatter key and omit the `policy` block.

A skill is user-invoked in every host or in none. `scripts/audit_portability.py`
enforces that agreement; a skill carrying one spelling without the other fails
the audit.

## Why two spellings

Invocation policy is portable behavior with a per-host encoding, not a
provider-specific feature:

| Host | Where user-only invocation is declared |
| --- | --- |
| Claude Code | `disable-model-invocation: true` in `SKILL.md` frontmatter |
| Cursor | `disable-model-invocation: true` in `SKILL.md` frontmatter |
| Codex | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` |
| Generic | No declaration; the description is the only gate |

Both spellings ship inside the skill package, so a linked installation works
without copying or rewriting files: Claude Code and Cursor read the frontmatter,
Codex reads the sidecar, and each ignores the other.

`disable-model-invocation` is therefore an allowed frontmatter key alongside
`name` and `description`. It is the only one. Write it as `true` or omit it;
`false` is the default and must not be spelled out.

On a host with no first-class declaration the model can reach any skill, and the
description is the only remaining gate. Do not claim enforcement there.

## Every skill carries a Codex sidecar

`agents/openai.yaml` is required for all skills, not only user-invoked ones,
because it also carries the Codex skill-picker metadata:

```yaml
interface:
  display_name: "Blast Radius"
  short_description: "Find what a change could break"
policy:
  allow_implicit_invocation: false
```

`interface.display_name` and `interface.short_description` are always required.
`policy` appears only on user-invoked skills.

## Choosing a mode

The test is: **could the model usefully reach for this on its own?**

Reuse is not the test. A skill extracted only to avoid repeating text can still
be user-invoked.

Prefer user-invoked when the skill takes an action with side effects, when
timing is the human's call, or when firing it unasked would derail work already
in progress. Prefer model-invoked for reference material the model should
consult when the subject comes up.

The current split is deliberate: 40 of 45 skills are user-invoked. The five the
model may reach for on its own are `comment-sicko`, `how`,
`typescript-best-practices`, `unslop`, and `why`.

All but one of these follow upstream. `setup-dstack` is the deliberate
divergence: upstream leaves its setup skill model-invocable, but configuring
host selection and role bindings is the human's call, and other skills already
tell the user to run it by name rather than calling it.

## The description is typed by the mode

- **User-invoked**: the description is **human-facing**. It is a one-line
  summary read by a person browsing slash commands. Strip trigger lists.
- **Model-invoked**: the description is **model-facing**. Keep rich trigger
  phrasing so auto-invocation actually fires.

Several inherited user-invoked skills still carry model-facing trigger lists.
That is a known inconsistency, tracked in `REMAINING.md`, not a licence to copy
the pattern into new skills.

## Dependencies between skills

A skill that needs another skill's work says so as an explicit instruction to
call the skill tool by name, not as a `../other-skill/SKILL.md` path and not as
a bare `/name` left for the model to interpret. Naming the operation is what
gets it run; a skill name without a leading slash also carries no assumption
about which host's trigger syntax it belongs to.

One skill per call. A step needing two skills is two calls.

This applies to **operative** instructions, where a skill's own steps send the
agent to run another skill now. Prose that merely names skills for a human to
pick from is not invoking anything.

**A user-invoked skill can never be reached this way.** No skill can call one,
by any spelling. When a step's precondition is a user-invoked skill, write it as
an instruction for the human: "tell the user to run `/setup-dstack`", never as a
call.

Shared reference material lives inside the skill that owns it. Other skills
reach it by calling that skill, not by linking across skill directories.
