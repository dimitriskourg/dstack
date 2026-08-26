# Skill invocation metadata

Skills that require explicit user invocation declare `disable-model-invocation: true`. Their `agents/openai.yaml` sidecar also sets `policy.allow_implicit_invocation: false`. The portability audit requires both declarations to agree.

Skills without either restriction remain available to the model and user. This is also the required state for an internal callee: a model-disabled skill cannot be reached through the Skill tool in Claude Code or Codex. Neither host provides a portable third state for a skill hidden from automatic selection but callable by another skill.

The currently bundled Skill Creator validator does not recognize `disable-model-invocation`, even though the target non-Codex harnesses use it. Run the validator and record that known rejection, but do not remove the field. `scripts/audit_portability.py` enforces agreement between the frontmatter and sidecar.

When a skill tells an agent to invoke another skill, use exactly:

```text
Call the Skill tool with `skill-name`.
```

The named skill must omit both invocation restrictions. The portability audit treats this phrase as an invocation-graph edge and rejects a model-disabled target.

When a prerequisite must remain human-only, do not use the Skill-tool phrase. Tell the user to invoke `skill-name` explicitly instead; the active host owns the user-facing trigger syntax.
