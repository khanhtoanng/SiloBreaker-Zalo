---
name: sdlc-extended
description: Use for high-risk or materially ambiguous changes, migrations, breaking contracts, or work across systems that requires staged decisions, verification, and resume.
---

# SDLC Extended

Read the [shared policy](../../../.ai-sdlc/POLICY.md) and effective AGENTS.md.

1. **Resume and discover.** Reconcile the exact ticket and accepted revisions
   with each authorized root, live change, earlier findings, and outstanding
   gates. Preserve valid decisions and reopen only affected work. For new or
   changed scope, use Intent when the goal is open and Spec when behavior or
   criteria are open. Ask the highest-impact unresolved question after
   reading evidence. Record the owner decision in the existing authorized
   ticket, ADR, or change record.
2. **Plan.** Have Architect trace affected consumers and assess contracts,
   migration, authorization, privacy, rollback, and cross-system risks.
   Agree material choices with the accountable owners. Select observable
   test seams, vertical slices, and integration, security, migration,
   and rollback checks. Use distinct Intent, Spec, or Plan records only
   where each fills a durable evidence need and is authorized.
3. **Develop and verify.** Honor outstanding human or organizational gates
   and obtain the bounded code-edit grant. Build the authorized slices with
   public-behavior RED/GREEN where applicable. Run required checks and retain
   criteria coverage and snapshot-bound results.
4. **Review.** Use independent review of the actual changes, contracts,
   test integrity, and rollout evidence. Have accountable humans inspect
   material decisions and risk-sensitive code/tests before acceptance.
   Report missing verification, outstanding approvals, and the next
   authorized action.
