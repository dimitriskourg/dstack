# Skill invocation metadata

Skills that require explicit user invocation declare `disable-model-invocation: true`. Their `agents/openai.yaml` sidecar also sets `policy.allow_implicit_invocation: false`. The portability audit requires both declarations to agree.

Skills without either restriction remain available for automatic selection. Do not change invocation mode merely to match descriptive prose.

The currently bundled Skill Creator validator does not recognize `disable-model-invocation`, even though the target non-Codex harnesses use it. Run the validator and record that known rejection, but do not remove the field. `scripts/audit_portability.py` enforces agreement between the frontmatter and sidecar.

When a skill tells an agent to invoke another skill, use exactly:

```text
Call the Skill tool with `skill-name`.
```
