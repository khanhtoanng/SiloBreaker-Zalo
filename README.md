# LifeMate 2026

LifeMate is an offline Python CLI for Vietnamese voice-to-action requests. It
interprets a request with a local model, executes allowed actions through the
organizer's simulator, and writes the actual tool trace and state hash.

The application lives in [LifeMate/](LifeMate/README.md). Open that folder in
PowerShell before running the application commands.

| I want to | Start here |
| --- | --- |
| Learn how LifeMate works | [AI concepts through the code](LifeMate/docs/ai_for_software_engineers.md), then the [project roadmap](LifeMate/docs/milestones/README.md) and [architecture](LifeMate/docs/architecture.md) |
| Build and install the Python app | [Build and verify the package](LifeMate/docs/build.md) |
| Run the app and test it | [Local quickstart](LifeMate/docs/local_quickstart.md) for setup, the test suite, one real simulator call, and a local model pilot |
| Run full predictions or fine-tune | [Operator guide](LifeMate/docs/operator_guide.md) and [LoRA training guide](LifeMate/docs/local_training.md) |
| Prepare a competition delivery | [Offline container build](LifeMate/docs/offline_packaging.md) and [Zalo submission milestone](LifeMate/docs/milestones/06-zalo-submission.md) |

## Workspace layout

| Path | Contents |
| --- | --- |
| `LifeMate/` | Python source, scripts, configs, tests, and application docs |
| `train+public_test/train+public_test/` | Extracted organizer kit v3.2.0 with train and public-test assets. Pass this directory as `--data-root` |
| `train+public_test.zip` | Original organizer archive for re-extraction |
| `local_lifemate_artifacts/` | Earlier local replay, training data preparation, Ollama evidence, and the tokenizer used in the quickstart |
| `tools/` and `prepare_kit_review.py` | Kit inventory, SDK checks, and preparation of a limited review archive |

Keep the organizer kit, model weights, and run outputs outside the application
source tree. Follow the organizer's data-sharing terms when distributing a build.

## Original handoff references

- Product goals and acceptance criteria. [Intent](intent.md)
- Design proposals, score-sensitive cases, and the original delivery plan. [Technical specification](spec.md), [scoring edge cases](SCORING_EDGE_CASES.md), [implementation plan](implementation_plan.md)
- Findings from the initial train SDK review and how that review archive was made. [Verified kit findings](KIT_VERIFIED_FINDINGS.md), [kit access notes](KIT_ACCESS_NOTES.md)
- Research alternatives and source inputs. [Research notes](01_research_brainstorm.md), [research handoff](inputs/LifeMate_AI_Research_Handoff.md), [data notes](inputs/data.md)

See the [verification history](LifeMate/docs/verification.md) for recorded checks
and the [scorer parity notes](LifeMate/docs/scorer_parity.md) for the limits of
local proxy scoring.
