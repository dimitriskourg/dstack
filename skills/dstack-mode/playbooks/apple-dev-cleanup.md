### Apple development cleanup

**You own the machine-wide safety gate.** Reclaim disk used by stale Apple simulators, runtimes, Xcode build products, and device-support files. This playbook is explicit only. A request to clean repository files, branches, or worktrees does not authorize it.

1. Audit before proposing deletion. Record `df -h /`, the active Xcode path, booted simulators, installed devices and runtimes, and the size and age of each candidate directory. Resolve every path from Xcode or `xcrun`; never construct a broad deletion target from an unresolved variable or glob.
2. Separate candidates by recovery cost:
   - unavailable simulator devices and abandoned XCTest clones are cheap to recreate;
   - DerivedData and obsolete device-support files rebuild or redownload when needed;
   - simulator runtimes are large downloads and require the strongest justification.
3. Protect current work. Hold every booted simulator, runtime required by a current project, active DerivedData build, and candidate whose ownership is unclear. Name what is held and why.
4. Present the exact candidates, sizes, recovery consequences, and proposed commands. Get explicit approval before deleting machine-wide state. Approval for one category does not authorize another.
5. Delete only the approved targets with the narrowest native operation available, such as `xcrun simctl delete unavailable` or an exact runtime identifier. Prefer moving ordinary directories to Trash over permanent removal when practical. Never use a recursive deletion against a home directory, Xcode root, simulator root, unresolved variable, or glob.
6. Re-run the inventory and `df -h /`. Report what was removed, what was retained, space recovered, and how deleted state can be recreated.

**Reply:** disk usage before and after, approved targets removed, targets held back with reasons, space recovered, and recovery notes.
