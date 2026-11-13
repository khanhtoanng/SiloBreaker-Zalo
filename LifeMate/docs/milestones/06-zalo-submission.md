# 06. Package and submit to Zalo

[Roadmap](README.md) · [Previous milestone](05-optimization-and-training.md)

The organizer publishes three distinct deliverables. This milestone maps them to the current checkout and lists the work needed to produce them. Dates and times below are in Vietnam time.

| Deliverable | Where and when |
| --- | --- |
| Public-test `submission.jsonl` | **Submission** section of the LifeMate portal through **16 November 2026**, up to five public results per day |
| Frozen Docker solution | **Solution Submission** form by **16 November 2026 at 23:59**. The organizer accepts up to two submissions and evaluates the last one |
| Private-test `submission.jsonl` | Run the frozen solution after private test is released on **20 November 2026**. Submit the result by **23 November 2026 at 23:59** |

The LifeMate Submission Guidance tab lists the private release at 09:00, while the public event timeline lists 11:00. Confirm the release time on the signed-in portal or latest organizer notice. [LifeMate portal, Submission Guidance](https://challenge.zalo.ai/portal/lifemate) · [Event timeline](https://challenge.zalo.ai/#timeline)

## 1. Validate and upload the public result

Use the public run from [milestone 04](04-audio-and-evaluation.md). `submission.jsonl` is UTF-8 JSON Lines. The supplied public kit shows three fields per row, `id`, `tool_calls`, and `state_hash`. LifeMate validates those fields and requires every manifest ID in order. The organizer's SDK validator separately checks whether the submitted calls conform to the split catalog and are available to the sample.

```powershell
$Submission = Join-Path $Work 'runs\public-run001\submission.jsonl'
& $Python -m lifemate validate --data-root $Kit --split public_test --predictions $Submission --out "$Work\reports\public-run001-validation.json"

Push-Location -LiteralPath (Join-Path $Kit 'public_test')
try {
    & $Python -m zaic_tools --split public_test --root $Kit --validate $Submission
} finally {
    Pop-Location
}
```

Adjust `$Submission` to the actual output path. Look for `PASS` and 634 samples from LifeMate, and `634 lines checked, 0 schema errors` from the kit CLI. The kit CLI can print schema errors with a successful exit status. Upload the complete result in the signed-in portal and record the submission time and status.

## 2. Close the Docker gaps

The [current offline packaging guide](../offline_packaging.md) describes a local draft. Use the following competition requirements for the release image. [Organizer Docker guide, sections 3–7](https://dl-challenge.zalo.ai/2026/lifemate_argfzdgert/Docker_Guide_ZAC2026_LifeMate.pdf)

| Organizer requirement | Work needed in this checkout |
| --- | --- |
| Read `/data/private_test/` and use its SDK, catalog, manifest and audio | [Competition defaults](../../configs/inference.competition.json) select the mounted private split and all of its samples |
| Launch `/code/predict.sh` with no arguments and write `/result/submission.jsonl` | [predict.sh](../../predict.sh) loads the competition configuration by default. Place the application layout under `/code` and test the organizer's exact launch command |
| Run with local models, tokenizers and dependencies | Stage the pinned Qwen GGUF, PhoWhisper files and CUDA llama-server at the paths in the [competition run guide](../competition_run.md) |
| Print model load and prediction times and emit integer elapsed milliseconds per row | The competition configuration enables `time` in the result and prints timing totals. The public upload command uses the kit's three-field format |
| Launch JupyterLab and generate `/result/jupyter_submission.jsonl` | Install JupyterLab and ship [start_jupyter.sh](../../start_jupyter.sh) and [predict_notebook.ipynb](../../predict_notebook.ipynb). Run all cells to exercise the shared prediction path |
| Supply training reproduction instructions | [training_code/README.md](../../training_code/README.md) records the models, revisions, licenses, seeds and optional LoRA procedure |

The Rule tab specifies **under 6B total parameters**, **under 5B for the LLM**, a **16,384-token maximum LLM context**, and **30 seconds per sample**, with offline inference and deterministic decoding. Check model and dataset release dates against the stated cutoff before 26 October 2026 and verify licenses. Set seeds explicitly and verify repeatability. Measure model load separately and include the full sample path in timings. Verify settings on the release image because local development configurations can use longer limits. [LifeMate portal, Rule](https://challenge.zalo.ai/portal/lifemate)

The Rule tab lists an NVIDIA A30. The linked Docker guide lists an RTX 5090 and gives CUDA 13.2 instructions, with broader compatibility language earlier in the same guide. Use the guide's CUDA 13.2 packaging example as the release starting point and confirm the active scoring hardware with the organizer before relying on latency measurements. [LifeMate portal, Rule](https://challenge.zalo.ai/portal/lifemate) · [Organizer Docker guide, sections 3–5](https://dl-challenge.zalo.ai/2026/lifemate_argfzdgert/Docker_Guide_ZAC2026_LifeMate.pdf)

## 3. Prove the image can run and submit it

1. On Linux with NVIDIA GPU support, verify the image can see the GPU and that the documented launch works with networking disabled, a read-only data mount and a fresh writable result directory. Before private release, use a local rehearsal config to exercise the same workflow on the mounted public split with its own SDK. Measure long-history and multi-action scenarios. Repeat in a fresh output directory and compare the IDs, traces and hashes. Timing can vary across runs.
2. Run all notebook cells and compare the notebook result with the script output. Confirm both files' coverage, the required timing field, stdout timing, and zero schema errors on applicable kit checks. Inspect timeout and fatal-error handling across the full run.
3. Inspect the image contents for training instructions, offline inference assets and owned source. Exclude the downloaded organizer archive, protected split data, credentials and local diagnostic files. The organizer's test data and SDK arrive via the mount.
4. Export and verify the compressed image on a second machine. Compute the **MD5 of the compressed archive**, upload the archive to Google Drive, and enable the link access the organizer needs for downloading it. Submit that link and MD5 in **Solution Submission**. Record the archive, image identity and portal receipt. [Organizer Docker guide, sections 5 and 8](https://dl-challenge.zalo.ai/2026/lifemate_argfzdgert/Docker_Guide_ZAC2026_LifeMate.pdf)

```bash
docker save zac2026-teamname:v1 | gzip > zac2026_TeamName.tar.gz
md5sum zac2026_TeamName.tar.gz
docker load -i zac2026_TeamName.tar.gz
```

## 4. Run the private split after release

Use the submitted frozen image with the newly supplied `/data/private_test/` assets and a fresh output directory. Confirm manifest coverage and the required result format, submit through **Submission**, and record the receipt before the private deadline. The organizers rerun the submitted image for verification. [LifeMate portal, Rule and Submission Guidance](https://challenge.zalo.ai/portal/lifemate)

The competition launch scripts, timed writer and notebook are in the application source. Image preparation, target-GPU verification and portal submission are release steps.
