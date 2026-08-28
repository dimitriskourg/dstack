---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

Fan out N parallel workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

Spawn workers with the active harness's native subagent tool. Every supported harness can spawn subagents. Use the host's reported available child capacity when it exposes one; otherwise conservatively launch one worker at a time. Drain each bounded wave before starting the next. If a required worker is denied or drops out, retry it in a later wave, then run that slice in the current agent if it still cannot run. Do not silently reduce N. Report the number of parallel waves, any serialized fallback, and any lost independence.

## Configuration

Before using a profile, map the system-provided product identity to the canonical id `codex`, `claude`, or `cursor`, then read `~/.dstack/config.json` and select `hosts[<active-harness>]`. Never invent an alias or select another host entry. If the file is missing, unreadable, or invalid, the identity is unknown, its host entry is absent, or a required profile is missing or listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Every profile must provide a concrete model and effort pair; do not guess, omit, or inherit a binding.

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
5. Give each worker its own writable output outside the repository, such as `/tmp/swarm-<slug>/worker-<n>/`. Workers may fan out read-only repository analysis or independent external artifacts. Repository writers are serialized in the active checkout.

## Phase B: Fan out

Launch workers in bounded waves using the capacity rule above. Bind each general-purpose subagent to the chosen profile's model and effort. Every required slice runs even when N exceeds the first wave's capacity.

When a worker must start from a non-default pushed branch, name that branch in its brief.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a required worker drops out, retry or run that slice serially in the current agent. Do not report complete coverage with a missing required slice. For a best-of race, a dropout may reduce the candidate set only when the declared race rule permits it; note the reduction.

## Phase C: Aggregate

Read the terminal results. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
