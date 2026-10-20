---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

Spawn workers with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, run the affected slice in the current agent and report that it was serialized.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
4. Pick the worker model from your configured `feature-worker` role, or `fast-explorer` when the slice is read-only. For a model race, name each arm's profile up front. Pick each subagent's configured profile for the job, per the Subagents section of the **dstack-mode** skill.
5. Give each worker its own writable output outside the repository, such as `/tmp/swarm-<slug>/worker-<n>/`. Workers may fan out read-only repository analysis or independent external artifacts. Repository writers are serialized in the active checkout. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method (sample count, what one sample is, order). The worker records both in its result.

## Phase B: Fan out

Launch workers in bounded waves that fit the active harness's available child capacity. Call the Skill tool with `dstack-config`. Name each worker's profile, and bind each general-purpose subagent to the values it returns. Every required slice runs even when N exceeds the first wave's capacity.

When a worker must start from a non-default pushed branch, name that branch in its brief.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

If a required worker drops out, retry or run that slice serially in the current agent. Do not report complete coverage with a missing required slice. For a best-of race, a dropout may reduce the candidate set only when the declared race rule permits it. Note the reduction.

## Phase C: Aggregate

Read the terminal results. Drop a result that does not record the SHAs and method its brief names, and respawn that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
