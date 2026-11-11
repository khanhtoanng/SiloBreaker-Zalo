"""One-off bounded r2 command evidence; no real data/model/runtime jobs."""
import json
import os
from pathlib import Path
import subprocess
import sys

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
phase = sys.argv[1]
out = WORK / "verification-r2" / phase
out.mkdir(parents=True, exist_ok=False)
python = ROOT / ".venv-core/Scripts/python.exe"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PIP_CACHE_DIR=str(ROOT / ".venv-core/pip-cache"))
focused = [("normalize", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_normalize.py", "-v"]), ("asr-metrics", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_asr_metrics.py", "-v"]), ("actual-consumers", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_cli.py", "-v"]), ("review-probes", [str(WORK / "review.r1.probes.py")])]
complete = [("pip-check", ["-m", "pip", "check"]), ("unittest", ["-m", "unittest", "discover", "-s", "tests", "-v"]), ("compileall", ["-m", "compileall", "-q", "src", "scripts", "tests"]), ("ruff-check", ["-m", "ruff", "check", "src", "scripts", "tests"]), ("ruff-format", ["-m", "ruff", "format", "--check", "src", "scripts", "tests"]), ("mypy", ["-m", "mypy", "src/lifemate"]), ("build", ["-m", "build", "--no-isolation"])]
help_commands = [("help", ["-m", "lifemate", "--help"]), ("train-help", ["-m", "lifemate", "train", "--help"]), ("legacy-predict-help", ["scripts/lifemate.py", "predict", "--help"]), ("train-wrapper-help", ["scripts/train_lora.py", "--help"]), ("predict-wrapper-help", ["scripts/predict.py", "--help"]), ("package-wrapper-help", ["scripts/verify_package.py", "--help"]), ("trajectories-help", ["scripts/check_trajectories.py", "--help"]), ("evaluator-help", ["scripts/check_evaluator.py", "--help"]), ("smoke-help", ["scripts/smoke_runtime.py", "--help"])]
commands = [("self-review", [str(WORK / "implementation_self_review_r2.py")])] if phase.startswith("audit") else focused if phase.startswith("focused") else complete + help_commands
records = []
for index, (name, args) in enumerate(commands, 1):
    command = [str(python), *args]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = out / f"{index:02d}-{name}.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    records.append({"command": command, "cwd": str(ROOT), "exit_code": result.returncode, "log": str(log.relative_to(ROOT))})
    if name == "review-probes" and result.returncode == 0:
        (out / "review-probes.json").write_text(json.dumps(json.loads(result.stdout), indent=2), encoding="utf-8")
    print(f"{name}: {result.returncode}", flush=True)
(out / "summary.json").write_text(json.dumps({"python": sys.version, "environment": {key: env[key] for key in ("PYTHONDONTWRITEBYTECODE", "PIP_CACHE_DIR")}, "records": records}, indent=2), encoding="utf-8")
raise SystemExit(int(any(r["exit_code"] for r in records)))
