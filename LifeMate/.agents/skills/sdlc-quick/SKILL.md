---
name: sdlc-quick
description: Use for a clear, local, reversible bug fix or small low-risk change, including resuming an existing ticket within that scope.
---

# SDLC Quick

Read the [shared policy](../../../.ai-sdlc/POLICY.md) and effective AGENTS.md.

1. **Resume and discover.** For existing work, recover the ticket, accepted
   decisions, current snapshot, and next unfinished action before questioning
   or editing. Inspect the relevant code and tests. Establish the intended
   behavior, a relevant negative or regression case, and the limited blast
   radius. A clear request needs no discovery question. If a consequential
   gap or higher risk emerges, investigate, ask the material question when
   needed, and recommend Standard or Extended before affected edits.
2. **Develop.** Once the bounded code-edit grant is established, use the
   smallest complete change. Reproduce a testable bug at a public seam,
   observe the intended RED and GREEN, and rerun after any refactor.
   Use characterization for behavior-preserving changes.
3. **Verify and review.** Run affected and mandatory checks. Pass the current
   change, criteria, and actual results to an independent Reviewer. Carry
   out required human acceptance for the reviewed snapshot. Use the existing
   ticket or PR for durable decisions and evidence when authorized.
