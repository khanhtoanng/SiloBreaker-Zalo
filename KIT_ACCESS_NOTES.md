> **Resolved in part (2026-11-09):** The user uploaded `LifeMate_Kit_Review_Small.zip` and the **train** SDK/catalog were successfully inspected. Read `KIT_VERIFIED_FINDINGS.md` for authoritative source observations. The missing official scorer/public-test SDK still need verification. The rest of this document records the earlier access issue for provenance.

# LifeMate organizer ZIP: verified access status and review instructions

**Date:** 2026-11-09

## What was directly verified

- The user-provided Drive URL resolves to a raw ZIP file named `train+public_test.zip`.
- Google Drive reported file size: **876,430,231 bytes** (about 876 MB, or 836 MiB).
- The connected download method fails with a **256 MiB per-file ceiling** (HTTP 413). A second mounted-files method also failed (413). **No inner file of this archive was successfully inspected.**
- The Drive metadata indicates access for 'anyone with the link'. Since the competitor research and example public GitHub implementations warn against distributing the official training dataset, restrict link sharing if that matches your organizer agreement.
- Actual schemas, scorer code, simulator behavior and dataset counts remain **UNVERIFIED** until the smaller kit bundle can be reviewed.

## Safest path to kit-level review

1. Download the official ZIP to your **local workstation**.
2. Download `prepare_kit_review.py` from this package.
3. Run: `python prepare_kit_review.py "C:\\path\\to\\train+public_test.zip" --out LifeMate_Kit_Review_Small.zip`
4. Inspect `review_manifest.json` inside the new ZIP and confirm the organizer permits sharing SDK/catalog files.
5. Upload the smaller ZIP in this conversation. Do **not** upload application state, raw audio, scenario JSONL, model weights, or public/private test labels.

The script reads the archive directly, without expanding it to disk. It selects readme/rules/submission documentation, `VERSION`, tool catalogs, `zaic_tools/*.py`, and evaluator/validator source files where present. It excludes `*_environment`, `state.json`, WAVs, scenario JSONL, and label-bearing records. It sets a default 40 MiB uncompressed review ceiling and a 10 MiB per-file ceiling; files skipped due to size are listed in the report.

## Next review tasks (NOT complete)

- Inspect authoritative official `README.md`, per-split `zaic_tools`, tool catalogs, validator, scoring code and submission wrapper.
- Prove `env.validate` does not add a logged call; verify behavior of failed calls and how `x-one-of`, `x-ref`, and `x-match` are enforced.
- Establish exact scoring rules (especially empty calls, state hash, matching, invalid calls and asks) from the official evaluation implementation.
- Convert these into executable gold-replay and edge-case tests and revise `intent.md`, `spec.md`, `implementation_plan.md` accordingly.

## Public references (context only; NOT proof about inner ZIP)

- Organizer task page: https://challenge.zalo.ai/portal/lifemate
- Competition schedule: https://challenge.zalo.ai/
- Participant audit (secondary evidence): https://github.com/AIVIETNAM-AIO-Dewey/Zalo-AIC-2026-Lifemate
