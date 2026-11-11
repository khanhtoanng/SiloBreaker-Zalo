---
name: sdlc-standard
description: Use for ordinary features and moderate changes that need observable acceptance criteria, a short technical plan, and verified delivery or ticket resume.
---

# SDLC Standard

Read the [shared policy](../../../.ai-sdlc/POLICY.md) and effective AGENTS.md.

1. **Resume and discover.** Recover the ticket, accepted decisions and
   criteria, actual change, and evidence-based next action before questioning
   or editing. For new or changed behavior, inspect the ticket, source,
   callers, contracts, and tests. Route one unresolved material product
   question through the coordinator and retain the answer in the existing
   record when authorized. Reassess profile if risk or scope increases.
2. **Specify and plan.** Use Spec for missing observable criteria. Use
   Architect to identify impact, affected callers and contracts, public test
   seams, the first failing behavior, and ordered vertical slices. Reuse the
   ticket or PR. Consider one short change.md only when an authorized durable
   record is needed and the existing record is insufficient.
3. **Develop and verify.** After the bounded code-edit grant, implement
   authorized slices using behavior-first TDD where feasible. Run relevant
   regression and mandatory checks, and map actual results to the criteria.
4. **Review.** Send the current change, accepted decisions, test evidence, and
   risks to an independent Reviewer. Recheck repairs and obtain required
   human acceptance on the reviewed snapshot.
