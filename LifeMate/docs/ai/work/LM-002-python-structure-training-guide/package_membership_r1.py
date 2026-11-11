"""Corrected one-off archive inspector; no models or external inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import os
import tarfile
import zipfile
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).parent/"verification-r1"
PYTHON=ROOT/".venv-core/Scripts/python.exe"
env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8",PIP_CACHE_DIR=str(ROOT/".venv-core/pip-cache"))
# Guide content changed after first successful build; rebuild only affected artifact.
command=[str(PYTHON),"-m","build","--no-isolation"]
result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
(OUT/"16-build-after-guide-adjustment.log").write_text(result.stdout+result.stderr,encoding="utf-8")
assert result.returncode==0,result.stderr
archives=[]
for path in sorted((ROOT/"dist").iterdir()):
    if path.suffix==".whl":
        with zipfile.ZipFile(path) as archive:names=archive.namelist()
        owned=[n for n in names if ".dist-info/" not in n]
        assert owned and all(n.startswith("lifemate/") and (n.endswith(".py") or n.endswith("py.typed")) for n in owned)
        relative=names
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path) as archive:names=archive.getnames()
        relative=[n.split("/",1)[1] for n in names if "/" in n]
        for required in ("configs/training.lora.json","docs/local_training.md","predict.sh","Dockerfile",".dockerignore","MANIFEST.in"):
            assert required in relative,required
    else:continue
    for name in relative:
        parts=Path(name).parts
        assert not any(p in {".venv",".venv-core","__pycache__","zaic_tools","models","local_artifacts",".mypy_cache",".ruff_cache"} or p.endswith("_environment") for p in parts),name
        assert not name.startswith(("docs/ai/","data/")),name
        assert not name.endswith((".pyc",".wav",".safetensors",".gguf",".bin",".pt")),name
    archives.append({"path":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"members":names})
assert len(archives)==2
(OUT/"archives.json").write_text(json.dumps(archives,indent=2),encoding="utf-8")
(OUT/"package-membership.json").write_text(json.dumps({"status":"PASS","corrected_checker":"Checks top-level data root and external asset components; owned lifemate/data Python is allowed","rebuild_command":command,"exit_code":result.returncode,"archives":[{k:v for k,v in a.items() if k!="members"} for a in archives]},indent=2),encoding="utf-8")
print(json.dumps({"package_membership":"PASS","archives":[{"path":a["path"],"sha256":a["sha256"],"members":len(a["members"])} for a in archives]},indent=2))
