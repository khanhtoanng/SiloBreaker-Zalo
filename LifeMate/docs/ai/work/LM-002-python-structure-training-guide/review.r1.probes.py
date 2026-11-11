"""Independent authored software probes; no organizer records or runtimes."""
import json
import runpy
import sys
import tempfile
import subprocess
from pathlib import Path
from lifemate.runtime.normalize import normalize

context = {"current_time": "2026-11-10T10:00:00+07:00", "timezone": "Asia/Ho_Chi_Minh"}
cases = {
    "compound_amount": "chuyển mười ba triệu cho mẹ",
    "negative_amount": "chuyển -500 nghìn",
    "separate_days": "đặt nhắc việc hôm nay 17 giờ và mai 8 giờ",
    "local_correction": "chuyển 500 nghìn và đặt xe năm giờ à không, năm rưỡi",
}
records = {key: normalize(text, context) for key, text in cases.items()}
sys.path.insert(0, "tests")
from test_runtime import CATALOG, SAMPLE, FakeEnv
from lifemate.runtime.loop import infer
ReadOnce = runpy.run_path("scripts/smoke_runtime.py", run_name="independent_read_only_import")["ReadOnce"]
env = FakeEnv()
prediction, diagnostic = infer(SAMPLE, ".", "train", CATALOG, ReadOnce("contacts.search"), env_factory=lambda *_: env)
records["runtime_smoke_read_once"] = {
    "prediction": prediction,
    "stop_reason": diagnostic["stop_reason"],
    "steps": diagnostic["steps"],
}
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    kit = root / "kit"
    split = kit / "train"
    split.mkdir(parents=True)
    (split / "train_tools_catalog.json").write_text(json.dumps({"apps": [
        {"id": app, "tools": [tool for tool in CATALOG.values() if tool["app"] == app]}
        for app in ("contacts", "sms", "sys")
    ]}), encoding="utf-8")
    rows = [{"id": "a"}, {"id": "b"}]
    manifest = split / "train.jsonl"
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    from lifemate.provenance import file_sha256
    fold = root / "fold.json"
    fold.write_text(json.dumps({"source_split": "train", "seed": 1,
        "dataset_sha256": file_sha256(manifest), "fit_ids": ["a"], "validation_ids": ["b"]}), encoding="utf-8")
    trajectories = root / "trajectories.jsonl"
    trajectories.write_text("".join(json.dumps({
        "scenario_id": sid, "partition": partition, "source_split": "train", "fold": "grouped", "step_index": 0,
        "messages": [{"role": "system", "content": "fixture"},
                     {"role": "user", "content": '{"observations":[]}'},
                     {"role": "assistant", "content": '{"kind":"DONE"}'}],
    }) + "\n" for sid, partition in (("a", "fit"), ("b", "validation"))), encoding="utf-8")
    output = kit / "forbidden-report.json"
    result = subprocess.run([sys.executable, "scripts/check_trajectories.py", "--data-root", str(kit),
        "--split-config", str(fold), "--trajectories", str(trajectories), "--out", str(output)],
        capture_output=True, text=True)
    records["utility_output_inside_kit"] = {"exit_code": result.returncode,
        "output_created_inside_protected_kit": output.exists(), "stdout": result.stdout, "stderr": result.stderr}
print(json.dumps(records, ensure_ascii=True, indent=2))
