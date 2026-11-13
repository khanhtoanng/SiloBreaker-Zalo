# Built-in TDD — test-first development, independent of external skills

This is a **normative runtime contract**, not an external skill installation. The installed `sdlc-work` references this contract directly; adapt execution to observed project tests without copying this file into project repositories. For executable behavior changes and reproducible bug fixes, default to a grounded RED → GREEN → REFACTOR slice where a real test seam exists. Do not weaken the existing test suite or accepted behavior just to achieve a shorter diff.

## Architect: choose a public test seam before editing

- Trace the accepted observable ACs or the actual reproduced bug to public/system-visible behavior. Prioritize practical unit, component, integration or contract seams already used in the repository; do not make breaking API changes merely to enable TDD.
- Slice work into the **smallest complete vertical behaviors**, including credible denied/invalid and data-integrity consequences. `coverage.md` decides whether a case is a distinct AC or just a VERIFY example; avoid writing a test for each speculative input permutation.
- In the plan-only phase propose test seams and needed existing commands, but do **not** write tests until the owner grants separate bounded code-edit authorization.

## Developer: one behavior slice at a time

1. **RED:** Write *one* meaningful test derived from accepted behavior, verified contract or a reproduced regression. Execute it and observe a failure **for the intended behavioral reason**, not missing dependencies, import errors, timing, environment failures or an incorrect expectation. For a bug, capture the failing regression first where feasible.
2. **GREEN:** Implement the smallest safe complete change that makes this test pass. Re-run the test and record the actual result. Do not create every speculative test before implementing the first slice.
3. **REFACTOR (only if justified):** Simplify while green. Preserve meaningful assertions, project idioms, security/data/error handling, and re-run relevant checks. Refactoring is an optional activity, not license to skip verification.
4. Repeat for the next accepted behavior. At completion run relevant authorized regression, lint/type/static/integration/security checks. Parameterize equivalent inputs when it improves evidence; do not duplicate the same invariant across every layer without benefit.

**Exception handling:** Pure documentation, text-only configuration, mechanical renaming or behavior-preserving refactoring may use appropriate pre/post checks instead of artificial RED. If a test runner or seam is unavailable, describe the blocker and use approved alternative characterization, integration or manual evidence. Never falsely claim a RED/GREEN execution. A risky change lacking adequate tests cannot pass merely because TDD was marked unavailable; escalate the verification gap and approval gate.

## Reviewer: evidence, not a TDD label

Check that recorded RED was the **expected test failure**, GREEN passed after the fix, any refactor was rerun, and assertions actually detect plausible incorrect behavior rather than implementation-call counts or tautologies. Confirm tests cover affected ACs and meaningful risk cases on the current snapshot. Report `TDD: BUILT_IN | UPSTREAM | NOT_APPLICABLE | NOT_RUN` and evidence/exception; where no tool run can be verified, use `NOT_RUN` regardless of prose claims. Missing required verification blocks `AI_PASS`.

**Evidence (reuse an existing ticket/PR/change record; no mandatory new report file):** AC or regression ID, small test seam, exact RED command/result/failure reason, GREEN command/result, refactor rerun (if any), final meaningful checks, TDD status and limitations.

## External TDD skill coexistence

Matt Pocock's upstream `tdd` skill is **separate and optional**. Only when explicitly selected and installed, inspect the **current upstream instructions** and meet their preconditions. Follow its actual sequence and report `TDD: UPSTREAM`; do not label the built-in sequence as that upstream skill. Any external conflict with owner policy, accepted ACs, permissions or required verification must be resolved before execution, not silently ignored. The plugin default is `BUILT_IN`.
