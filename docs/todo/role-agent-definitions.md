# Role agent definitions for effort bindings

Status: open

## Problem

`~/.dstack/config.json` binds each semantic role to a model *and* an effort, but
the effort half is only honored on one of three call paths.

| Call path | Model | Effort |
| --- | --- | --- |
| Workflow `agent(prompt, {model, effort})` | yes | yes |
| Agent definition frontmatter (`.claude/agents/*.md`) | yes | yes |
| Agent tool direct spawn | yes | **no — no `effort` parameter** |

A direct subagent spawn silently drops the configured effort and inherits the
parent's instead. Nothing errors, so the degradation is invisible.

## Task

Generate six agent definitions under `.claude/agents/`, one per role, each
carrying its model and reasoning effort in frontmatter, so `agentType: '<role>'`
binds both values on every path.

Current bindings for the `claude-code` host:

| Role | Model | Effort |
| --- | --- | --- |
| `fast-explorer` | sonnet | high |
| `feature-worker` | fable | medium |
| `bug-worker` | fable | medium |
| `deep-judgment` | fable | medium |
| `skeptical-reviewer` | fable | medium |
| `independent-judge` | opus | high |

Read the bindings from `config.json` at generation time rather than copying this
table; it is a snapshot from 2026-08-19 and `setup-dstack` may have changed them
since.

## Check first

Re-read the Agent tool schema before starting. If it has gained an `effort`
parameter, direct spawns can bind effort on their own and this task should be
deleted rather than done.

## Open question

Whether these definitions belong in the repo's `.claude/agents/` (shared, but
pins models for every user of the repo) or in `~/.claude/agents/` (personal,
matches where `config.json` already lives). The role bindings are personal
configuration, which argues for the latter.
