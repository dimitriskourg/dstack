---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

Fan out N parallel workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

Spawn workers with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, run the affected slice in the current agent and report that it was serialized.

## Configuration

Before using a profile, read `~/.dstack/config.json` and select `hosts[<active-harness>]` using the lowercase identity of the active harness. This location and host selection rule are fixed; do not use an environment override or another host entry. If the file is missing, unreadable, or invalid, the active harness cannot be identified, its host entry is absent, or a required profile is missing or listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Every profile must provide a concrete model and effort pair; do not guess, omit, or inherit a binding.

Apply the profile through `worker_binding`: pass its exact model and effort for `spawn-arguments`; for `worker-definitions`, spawn `dstack-<profile>` without overrides. Stop if the binding is missing, rejected, or different. Never inherit session effort.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers, not your host's concurrency limit.
4. Pick the worker model from your configured `feature-worker` role, or `fast-explorer` when the slice is read-only. For a model race, name each arm's binding up front.
5. Give each worker its own writable output when it writes. Use a worktree, branch, or `/tmp/swarm-<slug>/worker-<n>/`.

## Phase B: Fan out

Spawn all N workers at once as general-purpose subagents bound to the chosen profile's model and effort, in the background where your host supports it.

When a worker must start from a non-default pushed branch, name that branch in its brief.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
