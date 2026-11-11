"""Read-only independent snapshot/archive/test-integrity audit."""
import ast
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tarfile
import zipfile

root = Path.cwd().resolve()
work = root / "docs/ai/work/LM-002-python-structure-training-guide"
sha = lambda value: hashlib.sha256(value).hexdigest()
canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
spec = importlib.util.spec_from_file_location("independent_snapshot_reader", work / "snapshots/capture_lm002.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
report = {"stores": {}, "inputs": {}, "test_integrity": {}, "archives": [], "changed_paths": []}
manifests = {}
protected_manifests = {}
for tag in ("before-20261110-ap03-eg01-02", "after-20261110-r1"):
    store = work / "snapshots" / tag
    report["stores"][tag] = {}
    for scope in ("application", "protected"):
        path = store / scope / "manifest.json"
        manifest = json.loads(path.read_bytes())
        identity = {key: manifest[key] for key in ("schema", "root", "records")}
        assert sha(canonical(identity)) == manifest["identity_sha256"]
        for row in manifest["records"]:
            if row["type"] == "file":
                data = (store / scope / "files" / row["path"]).read_bytes()
                assert len(data) == row["length"] and sha(data) == row["sha256"]
        report["stores"][tag][scope] = {"identity": manifest["identity_sha256"], "manifest_sha256": sha(path.read_bytes()), "records": len(manifest["records"])}
        if scope == "application":
            manifests[tag] = {row["path"]: row for row in manifest["records"]}
        else:
            protected_manifests[tag] = {row["path"]: row for row in manifest["records"]}
before = manifests["before-20261110-ap03-eg01-02"]
after = manifests["after-20261110-r1"]
live, _, _ = capture.inventories()
records = []
for path, row in live:
    if row["type"] == "file":
        row["sha256"] = sha(path.read_bytes())
    records.append(row)
assert sorted(records, key=lambda row: row["path"]) == sorted(after.values(), key=lambda row: row["path"])
report["live_matches_after"] = True
protected_before = protected_manifests["before-20261110-ap03-eg01-02"]
protected_after = protected_manifests["after-20261110-r1"]
changed_protected = []
for path, row in protected_before.items():
    if row["type"] != "file":
        continue
    if protected_after.get(path) != row:
        changed_protected.append(path)
    if not path.endswith("/progress.md"):
        assert sha((root / path).read_bytes()) == row["sha256"], path
assert changed_protected == ["docs/ai/work/LM-002-python-structure-training-guide/progress.md"], changed_protected
report["preexisting_protected_changes"] = changed_protected
report["changed_paths"] = [path for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)]
report["changed_files"] = [path for path in report["changed_paths"] if after.get(path, before.get(path))["type"] == "file"]
for name in ("source.md", "intent.md", "spec.md", "plan.md", "implementation.md", "implementation-full-diff-r1.patch"):
    report["inputs"][name] = sha((work / name).read_bytes())
for name in ("test_runtime.py", "test_ollama.py", "test_sdk_contract.py"):
    old = ast.parse((work / "snapshots/before-20261110-ap03-eg01-02/application/files/tests" / name).read_text(encoding="utf-8"))
    new = ast.parse((root / "tests" / name).read_text(encoding="utf-8"))
    old_tests = {node.name for node in ast.walk(old) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    new_tests = {node.name for node in ast.walk(new) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    def assertions(tree):
        return Counter(ast.dump(node, include_attributes=False) for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert"))
    missing = assertions(old) - assertions(new)
    assert not old_tests - new_tests and not missing
    report["test_integrity"][name] = {"original_methods": len(old_tests), "current_methods": len(new_tests), "original_assertions_retained": sum(assertions(old).values()), "missing": []}
matrix = (root / "docs/edge_case_coverage.md").read_text(encoding="utf-8")
assert all(len(re.findall(r"\| K" + str(i).zfill(2) + r" \|", matrix)) == 1 for i in range(1, 55))
references = sorted(set(re.findall(r"test_\w+\.\w+\.test_\w+", matrix)))
for reference in references:
    module, cls, method = reference.split(".")
    tree = ast.parse((root / "tests" / (module + ".py")).read_text(encoding="utf-8"))
    assert any(isinstance(node, ast.ClassDef) and node.name == cls and any(isinstance(child, ast.FunctionDef) and child.name == method for child in node.body) for node in tree.body)
report["K01_K54_unique_rows_and_executable_references"] = len(references)
for archive in sorted((root / "dist").iterdir()):
    if archive.suffix == ".whl":
        with zipfile.ZipFile(archive) as stream:
            members = stream.namelist()
            owned = [name for name in members if name.startswith("lifemate/") and not name.endswith("/")]
            for name in owned:
                assert stream.read(name) == (root / "src" / name).read_bytes()
            assert all(name.startswith("lifemate/") or ".dist-info/" in name for name in members)
    elif archive.name.endswith(".tar.gz"):
        with tarfile.open(archive) as stream:
            members = stream.getnames()
            owned = []
            for member in stream.getmembers():
                if not member.isfile():
                    continue
                relative = Path(*Path(member.name).parts[1:])
                if str(relative).startswith(("src/lifemate.egg-info", "src\\lifemate.egg-info")) or relative.as_posix() in ("PKG-INFO", "setup.cfg"):
                    continue
                assert (root / relative).is_file(), relative
                assert stream.extractfile(member).read() == (root / relative).read_bytes(), relative
                owned.append(relative.as_posix())
            assert not any("docs/ai/" in name or "/models/" in name or "/.venv" in name for name in members)
    else:
        continue
    report["archives"].append({"path": archive.relative_to(root).as_posix(), "sha256": sha(archive.read_bytes()), "owned_byte_matches": len(owned), "members": members})
print(json.dumps(report, ensure_ascii=True, indent=2))
