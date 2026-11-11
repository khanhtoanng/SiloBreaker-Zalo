"""One-off Developer command evidence. No model or real-data runtime is invoked."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[4]
PYTHON=ROOT/".venv-core/Scripts/python.exe"
OUT=Path(__file__).parent/"verification-r1"
OUT.mkdir(exist_ok=False)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8",PIP_CACHE_DIR=str(ROOT/".venv-core/pip-cache"))
commands=[("pip-check",["-m","pip","check"]),("unittest",["-m","unittest","discover","-s","tests","-v"]),("compileall",["-m","compileall","-q","src","scripts","tests"]),("ruff-check",["-m","ruff","check","src","scripts","tests"]),("ruff-format",["-m","ruff","format","--check","src","scripts","tests"]),("mypy",["-m","mypy","src/lifemate"]),("build",["-m","build","--no-isolation"]),("help",["-m","lifemate","--help"]),("train-help",["-m","lifemate","train","--help"]),("legacy-predict-help",["scripts/lifemate.py","predict","--help"]),("train-wrapper-help",["scripts/train_lora.py","--help"]),("predict-wrapper-help",["scripts/predict.py","--help"]),("package-wrapper-help",["scripts/verify_package.py","--help"]),("trajectory-wrapper-help",["scripts/check_trajectories.py","--help"]),("replay-wrapper-help",["scripts/replay_gold.py","--help"])]
records=[]
for index,(name,args) in enumerate(commands,1):
    command=[str(PYTHON),*args]
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
    log=OUT/f"{index:02d}-{name}.log"
    log.write_text(result.stdout+result.stderr,encoding="utf-8")
    records.append({"command":command,"cwd":str(ROOT),"exit_code":result.returncode,"log":str(log.relative_to(ROOT))})
    print(name+": "+str(result.returncode),flush=True)
archives=[]
for path in sorted((ROOT/"dist").iterdir()):
    if path.suffix==".whl":
        with zipfile.ZipFile(path) as archive:names=archive.namelist()
        owned=[n for n in names if ".dist-info/" not in n]
        assert owned and all(n.startswith("lifemate/") and (n.endswith(".py") or n.endswith("py.typed")) for n in owned),owned
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path) as archive:names=archive.getnames()
        stripped=[n.split("/",1)[1] for n in names if "/" in n]
        assert "configs/training.lora.json" in stripped and "docs/local_training.md" in stripped and "predict.sh" in stripped
    else:continue
    prohibited=("docs/ai/",".venv/",".venv-core/","data/","models/","local_artifacts/","__pycache__/",".pyc","zaic_tools/","_environment/")
    assert not any(any(part in n for part in prohibited) for n in names),names
    archive_record={"path":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"members":names}
    archives.append(archive_record)
assert len(archives)==2
(OUT/"archives.json").write_text(json.dumps(archives,indent=2),encoding="utf-8")
summary={"python":sys.version,"env":{"PYTHONDONTWRITEBYTECODE":"1","PIP_CACHE_DIR":env["PIP_CACHE_DIR"]},"records":records,"package_membership":"PASS","archives": [{k:v for k,v in a.items() if k!="members"} for a in archives]}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
raise SystemExit(0 if all(record["exit_code"]==0 for record in records) else 1)
