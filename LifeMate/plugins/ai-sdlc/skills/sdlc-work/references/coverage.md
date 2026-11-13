# Justified coverage — one rule set for edge cases and output length

Use this **before** Spec, Architect, Developer or Reviewer adds a requirement or test. No numeric minimum/maximum count of ACs or tests. Critical controls and unlikely high-impact risks override any writing brevity target.

## Classify only material candidates

| Class | Destination | Decision test |
|---|---|---|
| `REQUIRED` | Source-linked observable AC | Owner-accepted behavior, verified existing contract, or mandatory applicable control; a plausible new feature requires acceptance first |
| `VERIFY` | Test/example/check under an AC | Input, boundary, negative path, state or credible failure that checks an accepted rule; **not another AC** by default |
| `DECISION` | Coordinator asks owner | Consequential unresolved WHAT, data/rights, compatibility or scope changes expected result |
| `DEFER` | At most brief out-of-scope note | Adjacent useful but unrequested behavior not needed to deliver accepted outcome |
| `REJECT` | Omit | Unsupported speculation, redundant variants or irrelevant scenario |

`UNKNOWN` existing behavior must be investigated; don't assert it as verified REQUIRED. Do not defer a discovered vulnerability, loss-of-data hazard, mandatory compliance rule or serious broken existing contract for brevity.

## Five-question filter

1. **Grounded?** What accepted ticket/owner decision, observed code/interface, documented contract or mandatory safeguard requires this?
2. **Material?** Does failure significantly affect outcome, authorization, privacy, integrity, compatibility, accessibility, security, availability or recovery? High-impact rare risks still count.
3. **Distinct?** Is it a *different externally observable rule*, or merely another input that tests an existing rule? Merge equivalent inputs into VERIFY.
4. **Actionable?** Would documenting/testing it change a build, implementation, human decision or review action?
5. **Enough?** Stop once every accepted rule is testable, significant credible hazards considered, and further cases add no distinct rule/meaningful defect detection.

Use Example Mapping lightly: **Story → business Rules (ACs) → representative Examples (VERIFY) → consequential Questions (DECISION)**. Avoid speculative combinations and fake precision. When a new failure reveals a novel WHAT choice, Coordinator asks owner rather than silently imposing product behavior.

## Depth by mode

- **Quick:** known behavior + one meaningful check; no full Intent/Spec artifact.
- **Standard:** a few distinct current rules and grounded negative/boundary examples. Group related ACs by user outcome.
- **Extended:** additional evidence for *actual* sensitive paths, cross-service impacts, data migration/recovery, revoked access, compatibility and rollout. Multiple repos alone do not require Extended. Human summary stays short; supporting proof can be long.
- **Spike:** bounded question and decision brief, not preemptive AC inventory.

**Human-facing:** The summary maps explicitly to **every AC ID**. Full AC text and provenance stay in ticket/PR/current authorized record. The human reviews changed behavior, exclusions, material decisions and safety/rollout, not a mechanical list of every test input.
