"""One-off full live/baseline self-review evidence; creates no snapshot store."""
import ast
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import runpy
WORK=Path(__file__).resolve().parent
capture=runpy.run_path(str(WORK/"snapshots/capture_lm002.py"))
audit=runpy.run_path(str(WORK/"snapshots/audit_lm002.py"))
ROOT=capture["ROOT"]
BASE=WORK/"snapshots/before-20261110-ap03-eg01-02/application"
capture["verify_store"](BASE)
old_manifest=json.loads((BASE/"manifest.json").read_bytes())
old={r["path"]:r for r in old_manifest["records"]}
items,_,_=capture["inventories"]()
current={}
for path,row in items:
    if row["type"]=="file":row["sha256"]=capture["digest"](path.read_bytes())
    current[row["path"]]=row
changes=[];diff=[]
for name in sorted(old.keys()|current.keys()):
    a,b=old.get(name),current.get(name)
    if a==b:continue
    record=b or a
    permitted=name in audit["allowed"] or name.startswith("tests/fixtures/") or record["type"]=="directory" and any(p.startswith(name+"/") for p in audit["allowed"])
    assert permitted,name
    assert b is not None,"Unauthorized deletion: "+name
    changes.append({"path":name,"status":"ADDED" if a is None else "MODIFIED","before":a,"after":b})
    if record["type"]=="file":
        before=(BASE/"files"/name).read_text(encoding="utf-8").splitlines(keepends=True) if a is not None else []
        after=(ROOT/name).read_text(encoding="utf-8").splitlines(keepends=True)
        diff.extend(difflib.unified_diff(before,after,fromfile="before/"+name,tofile="after/"+name))
# All original test methods/assertions remain present; fixture additions are explicit.
test_integrity=[]
for name in ("tests/test_runtime.py","tests/test_ollama.py","tests/test_sdk_contract.py"):
    before=ast.parse((BASE/"files"/name).read_text(encoding="utf-8"));after=ast.parse((ROOT/name).read_text(encoding="utf-8"))
    def methods(tree):return {n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")}
    def assertions(tree):return Counter(ast.unparse(n) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith("assert"))
    missing=assertions(before)-assertions(after)
    assert not methods(before)-methods(after),name
    assert not missing,(name,missing)
    test_integrity.append({"path":name,"original_methods":len(methods(before)),"current_methods":len(methods(after)),"original_assertions":sum(assertions(before).values()),"current_assertions":sum(assertions(after).values()),"original_assertions_retained":True})
records=sorted(current.values(),key=lambda r:r["path"])
identity=capture["digest"](capture["canonical"]({"schema":capture["SCHEMA"],"root":str(ROOT),"records":records}))
output=WORK/"implementation-full-diff-r1.patch"
output.write_text("".join(diff),encoding="utf-8")
summary={"baseline_identity":old_manifest["identity_sha256"],"live_application_identity":identity,"baseline_files":sum(r["type"]=="file" for r in old.values()),"current_files":sum(r["type"]=="file" for r in current.values()),"changed_file_count":sum(c["after"]["type"]=="file" for c in changes),"added_files":sum(c["status"]=="ADDED" and c["after"]["type"]=="file" for c in changes),"modified_files":sum(c["status"]=="MODIFIED" and c["after"]["type"]=="file" for c in changes),"deletions":0,"out_of_grant":[],"changes":changes,"test_integrity":test_integrity,"diff_path":str(output.relative_to(ROOT)),"diff_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"diff_lines":len(output.read_text(encoding="utf-8").splitlines())}
(WORK/"implementation-diff-r1.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in summary.items() if k not in ("changes",)},indent=2))
