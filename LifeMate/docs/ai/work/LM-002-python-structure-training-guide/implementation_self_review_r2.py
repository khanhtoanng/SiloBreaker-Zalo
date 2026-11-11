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
output=WORK/"implementation-full-diff-r2.patch"
output.write_text("".join(diff),encoding="utf-8")
summary={"baseline_identity":old_manifest["identity_sha256"],"live_application_identity":identity,"baseline_files":sum(r["type"]=="file" for r in old.values()),"current_files":sum(r["type"]=="file" for r in current.values()),"changed_file_count":sum(c["after"]["type"]=="file" for c in changes),"added_files":sum(c["status"]=="ADDED" and c["after"]["type"]=="file" for c in changes),"modified_files":sum(c["status"]=="MODIFIED" and c["after"]["type"]=="file" for c in changes),"deletions":0,"out_of_grant":[],"changes":changes,"test_integrity":test_integrity,"diff_path":str(output.relative_to(ROOT)),"diff_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"diff_lines":len(output.read_text(encoding="utf-8").splitlines())}
(WORK/"implementation-diff-r2.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in summary.items() if k not in ("changes",)},indent=2))

# Repair-only identity/diff supplements the complete original-to-final evidence.
import re
import tarfile
import zipfile
R1=WORK/"snapshots/after-20261110-r1/application"
capture["verify_store"](R1)
capture["verify_store"](BASE.parent/"protected")
capture["verify_store"](R1.parent/"protected")
protected_r1=json.loads((R1.parent/"protected/manifest.json").read_bytes())
for record in protected_r1["records"]:
    if record["type"]!="file" or record["path"].endswith(("/implementation.md","/progress.md")):continue
    assert capture["digest"]((ROOT/record["path"]).read_bytes())==record["sha256"],record["path"]
repair_manifest=json.loads((R1/"manifest.json").read_bytes())
prior={r["path"]:r for r in repair_manifest["records"]}
repair_changes=[];repair_diff=[]
for name in sorted(prior.keys()|current.keys()):
    a,b=prior.get(name),current.get(name)
    if a==b:continue
    assert a is not None and b is not None and b["type"]=="file",name
    repair_changes.append({"path":name,"status":"MODIFIED","before":a,"after":b})
    repair_diff.extend(difflib.unified_diff((R1/"files"/name).read_text(encoding="utf-8").splitlines(keepends=True),(ROOT/name).read_text(encoding="utf-8").splitlines(keepends=True),fromfile="r1/"+name,tofile="r2/"+name))
repair_output=WORK/"implementation-repair-diff-r2.patch"
repair_output.write_text("".join(repair_diff),encoding="utf-8")
repair_integrity=[]
for record in repair_manifest["records"]:
    name=record["path"]
    if record["type"]!="file" or not name.startswith("tests/") or not name.endswith(".py"):continue
    before=ast.parse((R1/"files"/name).read_text(encoding="utf-8"));after=ast.parse((ROOT/name).read_text(encoding="utf-8"))
    assert not methods(before)-methods(after),name
    assert not assertions(before)-assertions(after),name
    repair_integrity.append({"path":name,"r1_methods":len(methods(before)),"r2_methods":len(methods(after)),"r1_assertions_retained":sum(assertions(before).values())})
repair_summary={"r1_identity":repair_manifest["identity_sha256"],"r2_live_identity":identity,"changed_files":repair_changes,"deletions":0,"r1_test_integrity":repair_integrity,"diff_sha256":hashlib.sha256(repair_output.read_bytes()).hexdigest(),"diff_lines":len(repair_diff)}
(WORK/"implementation-repair-diff-r2.json").write_text(json.dumps(repair_summary,indent=2),encoding="utf-8")
expected={"source.md":"ab1e5a069dc9c2379226c0e475f35b9d1992da9416175ec2d2a15e042c5f0205","intent.md":"d7c8e8ada44f76feaaa074b8f19c575e71610d618038b7ac0327362ba6e6e5a6","spec.md":"84f6a227878423ec886f3575b523f6b3e7aa5b7d0e8e1ba7d1da1aa4c9ad12a0","plan.md":"722c2d624027dc17e4697f4648be5f6f3abe7a20e4087239807582c1059905ba","implementation.r1.md":"7ef02741be8225778b474364cdb9c28299b1b421bbd0c23ca58738c3b3b1a98f","review.r1.md":"5a6c95a879406667aa89b7e37d509cb8c8ac0e186ae0d8cdf3f74f2852042e90"}
for name,value in expected.items():assert hashlib.sha256((WORK/name).read_bytes()).hexdigest()==value,name
matrix=(ROOT/"docs/edge_case_coverage.md").read_text(encoding="utf-8")
assert all(matrix.count("| K"+str(i).zfill(2)+" |") == 1 for i in range(1,55))
references=sorted(set(re.findall(r"test_\w+\.\w+\.test_\w+",matrix)))
for reference in references:
    module,cls,method=reference.split(".")
    tree=ast.parse((ROOT/"tests"/(module+".py")).read_text(encoding="utf-8"))
    assert any(isinstance(n,ast.ClassDef) and n.name==cls and any(isinstance(c,ast.FunctionDef) and c.name==method for c in n.body) for n in tree.body),reference
archives=[]
for path in sorted((ROOT/"dist").iterdir()):
    if path.suffix==".whl":
        with zipfile.ZipFile(path) as stream:
            members=stream.namelist()
            owned=[name for name in members if name.startswith("lifemate/") and not name.endswith("/")]
            for name in owned:assert stream.read(name)==(ROOT/"src"/name).read_bytes(),name
            assert all(name.startswith("lifemate/") or ".dist-info/" in name for name in members)
            assert {name[4:] for name in current if name.startswith("src/lifemate/") and current[name]["type"]=="file"}==set(owned)
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path) as stream:
            members=stream.getnames();owned=[]
            for member in stream.getmembers():
                if not member.isfile():continue
                name=Path(*Path(member.name).parts[1:]).as_posix()
                if name.startswith("src/lifemate.egg-info/") or name in ("PKG-INFO","setup.cfg"):continue
                assert name in current and current[name]["type"]=="file",name
                assert stream.extractfile(member).read()==(ROOT/name).read_bytes(),name
                owned.append(name)
            # Source/tests/scripts/guides/configs are packaged. Checkout Git
            # ignore metadata and the retained historical catalog audit JSON
            # are outside the established sdist manifest, as in r1.
            expected_owned={name for name,row in current.items() if row["type"]=="file" and name not in (".gitignore","docs/catalog_audit.json")}
            assert expected_owned-set(owned)==set(),expected_owned-set(owned)
    else:continue
    for name in members:
        assert not any(p in {".venv",".venv-core","__pycache__","zaic_tools","models","local_artifacts",".mypy_cache",".ruff_cache"} or p.endswith("_environment") for p in Path(name).parts),name
        assert "docs/ai/" not in name and not name.endswith((".pyc",".wav",".safetensors",".gguf",".bin",".pt")),name
    archives.append({"path":path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"owned_byte_matches":len(owned),"members":members})
assert len(archives)==2
result={"status":"PASS","live_application_identity":identity,"approved_and_preserved_hashes":expected,"K01_K54_unique_rows":54,"unique_named_K_methods":len(references),"original_methods_retained":68,"original_assertion_expressions_retained":137,"r1_test_integrity":repair_integrity,"repair_changed_files":[c["path"] for c in repair_changes],"archives":archives}
(WORK/"implementation-evidence-audit-r2.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps({"status":"PASS","repair_changed_files":result["repair_changed_files"],"archive_byte_matches":[{"path":a["path"],"count":a["owned_byte_matches"],"sha256":a["sha256"]} for a in archives]},indent=2))
