# Maintaining upstream alignment

Read [Supported scope](06-supported-scope.md) and [DIFFERENCES.md](../../DIFFERENCES.md). `DIFFERENCES.md` is the durable absorb contract. Copy only keep-set skills and playbooks from a new pstack version. Do not pull dropped items or recreate adapters. Apply only the standard token transforms recorded there.

Treat `/Users/kourgia/projects/plugins/pstack` and sibling plugin folders as immutable inputs. Use the local pstack checkout named in `DIFFERENCES.md` as the comparison tree.

Run the portability audit, unit tests, JSON validation, and Skill Creator validation for each changed skill. Follow with live harness checks for any behavior claim involving subagents, model selection, transcripts, UI, or long-running work.
