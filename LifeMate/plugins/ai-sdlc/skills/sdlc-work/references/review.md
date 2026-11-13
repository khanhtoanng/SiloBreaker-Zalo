# Human review contract — decision first, traceable detail underneath

## Who owns what

| Stage | AI prepares | Human must decide / review when material |
|---|---|---|
| Intent | short actor, outcome, scope and provenance | Is that the desired outcome/scope? Consequential unknowns only |
| Spec | complete source-linked ACs, grounded VERIFY cases, short full-AC map | Accept actual added/changed observable WHAT and non-goals, pinned to full AC revision |
| Architect | impacted code, minimal option/plan, risks and tests | Only significant architecture/security/data/rollout tradeoff |
| Developer | bounded diff, test commands/results and AC evidence | Separate scope-specific code edit authority; not inferred from Spec acceptance |
| Reviewer | independent current-snapshot findings and risks | Qualified final acceptance where risk/org rules require it; merge/deploy remain distinct actions |

If existing accepted information is current, **don't ask the human to approve it again**. Never ask a technical design approval for a routine low-risk code choice. No role can grant its own acceptance. Material questions go through Coordinator **one at a time**, after attempting to resolve them from evidence.

## Review card (normally 8–15 short lines; not a hard maximum)

Use ordinary business language, not a wall of XML tags, Gherkin or trace matrices. Put decision/changes first. Use this layout only when the stage actually requires human review:

**Outcome:** One sentence about who benefits and what changes.

**Proposed decisions (if any):** The *single* material choice, grounded alternatives/impact and one-line recommendation; show only if undecided. Never show a raw brainstorming transcript or repeat accepted decisions. Keep pending choices OUT of accepted AC text.

**Behavior to approve:** A small table grouped by outcome. Explicitly list or group **all** relevant changed AC IDs with one-line statements; each ID links/points to the full AC text and its source/revision. No unreferenced ACs in hidden detail.

**Not changing:** 1–3 important exclusions or compatibility guarantees, not exhaustive negative inventory.

**Risk / review level:** One or two meaningful risks and resulting gates, e.g. authorization, migration recovery. If ordinary low risk, say so and avoid a long risk register.

**Requested human action:** `Approve <AC revision>` or a single decision; **different** from separately granting file edits.

Detailed accepted ACs, observed tests, and diagnostics belong in the existing ticket/PR/change record, beneath/behind the short card. Always make the full AC revision accessible at approval. If the owner cannot inspect it, `AC_ACCEPTANCE: NOT VERIFIED`.

## Durable stage handoff (issue/PR or optionally one concise work record)

Keep, without duplicating in every stage file: source revision; accepted decisions/AC IDs and text; relevant design slices/test seams; authorized edit grant separately; changed snapshot; observed commands/outcomes; reviewer independence/findings; current owner approvals. Recheck staleness on resume. If no tracker exists and work spans sessions, propose ONE project-native `change.md` or equivalent with these headings **only if file writes are authorized**. Human review card is a navigation summary, never a substitute for full normative ACs.

## End-state status

- `ROLE READY` is only a worker's completion claim, not owner approval.
- `SPEC ACCEPTED` binds a specific complete AC set/revision.
- `EDIT AUTHORIZED` binds operations/path/roots separately.
- `AI_PASS` is an independent on-snapshot evidence verdict, not permission to merge or deploy.
- `HUMAN ACCEPTED` occurs only when the relevant authorized owner actually approves the reviewed snapshot.
