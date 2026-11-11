# Offline packaging and deferred release gates

For the organizer's actual input, output, and notebook requirements, use the
[Zalo submission milestone](milestones/06-zalo-submission.md). The commands
below describe the current generic container draft.

Dockerfile, .dockerignore, predict.sh and scripts/predict.py provide a static path.
No image build/run, model execution or official mount/entrypoint/resource
certification ran here. Default single-container policy is local Transformers plus
optional PEFT adapter and Whisper ASR. Ollama remains a host loopback option; its
service is not silently bundled. Kit, model/tokenizer/adapter/ASR and output are
explicit external mounts. No SDK/data/weights enter source/build context.

Prepare a reviewed complete local wheelhouse including setuptools/wheel and all
resolved model/asr runtime dependencies. Docker bootstraps setuptools/wheel using
--no-index, then installs owned source with --no-build-isolation from that wheelhouse.
No runtime model download occurs. Pin a reviewed base digest via BASE_IMAGE and
preload it. The default Python base tag is illustrative, not a certified GPU image;
review CUDA/driver/runtime separately. Record all wheels/licenses/image identities.

Copy/edit configs/inference.audio.json outside source. Example mounts /inputs/kit,
/models/base, /models/asr, /models/adapter and /outputs are not official mount names.
Public/private requires its selected split assets, audio/all and no test oracle.
WAVs currently support <=30 seconds per provided turn. Real preprocessing/model
compatibility still needs runtime evidence. Static commands:

```powershell
python -m lifemate package-check --config C:/LifeMateWork/configs/audio.json
python scripts/verify_package.py --config C:/LifeMateWork/configs/audio.json
python -m build --no-isolation
```

Package-check returns STATIC_ONLY and missing dependency names without loading
weights/tokenizer/session; missing assets fail. Inspect complete wheel/sdist member
lists: wheel owns lifemate Python/py.typed/distribution metadata; sdist also includes
owned docs/config/scripts/packaging. Exclude docs/ai/snapshots, organizer SDK/catalog,
audio/state/labels, models/adapters, environments/caches/local artifacts/credentials.
MANIFEST.in prunes boundaries, but archive inspection remains mandatory.

Later authorized Linux examples, after verifying exact organizer contracts:

```bash
docker build --network none --build-arg BASE_IMAGE='reviewed-base@sha256:REPLACE' -t lifemate:reviewed .
docker run --rm --network none --gpus all -v /authorized/kit:/inputs/kit:ro -v /reviewed/models:/models:ro -v /work/configs:/configs:ro -v /work/outputs:/outputs lifemate:reviewed --config /configs/audio.json
```

Build requires preloaded base/wheelhouse. predict.sh uses LF/shebang and exec python
-m lifemate predict, forwarding arguments; verify executable mode on later Linux.
Validate shape/exact IDs and organizer validator, inspecting printed errors plus exit
status. Measure complete startup/latest+history ASR/planning/generations/tools/
serialization, p50/p95/p99/max, peak memory/parameter totals, long history and six-call
cases. Test network disabled/no downloads/services and repeated manifest determinism.
Record code/config/model/tokenizer/adapter/image checksums and licensing. Software
review/owner acceptance do not substitute for these deferred release gates.
