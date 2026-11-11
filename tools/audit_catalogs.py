#!/usr/bin/env python3
"""Read organizer tool catalogs ONLY. Never reads samples, audio, state or environments.

Run from an authorized local competition workspace:
    python tools/audit_catalogs.py --data-root path/to/train+public_test --out docs/catalog_audit.json
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path


def summarize(path: Path):
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    apps, tools = doc.get("apps", []), [t for a in doc.get("apps", []) for t in a.get("tools", [])]
    prop_ext = collections.Counter()
    for t in tools:
        params = t.get("parameters") or {}
        if params.get("x-one-of"):
            prop_ext["x-one-of"] += 1
        for p in (params.get("properties") or {}).values():
            for k in ("x-ref", "x-match", "format", "enum", "minimum", "maximum"):
                if k in p:
                    prop_ext[k] += 1
    return {
        "catalog_file": str(path),
        "schema_version": doc.get("schema_version"),
        "apps_count": len(apps),
        "tools_count": len(tools),
        "kinds": dict(collections.Counter(t.get("kind", "UNKNOWN") for t in tools)),
        "annotations": dict(prop_ext),
        "app_ids": sorted(a.get("id") for a in apps),
        "tool_names": sorted(t.get("name") for t in tools),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", required=True, type=Path, help="folder containing train/ and public_test/")
    p.add_argument("--out", type=Path, help="output report; no raw data, state or labels")
    args = p.parse_args()
    reports = {}
    for split in ("train", "public_test", "private_test"):
        f = args.data_root / split / f"{split}_tools_catalog.json"
        reports[split] = summarize(f)
    train, public = reports["train"], reports["public_test"]
    if train and public:
        t, u = set(train["app_ids"]), set(public["app_ids"])
        reports["comparison"] = {
            "train_only_apps": sorted(t - u), "public_only_apps": sorted(u - t),
            "shared_apps": sorted(t & u),
            "train_only_tools": sorted(set(train["tool_names"]) - set(public["tool_names"])),
            "public_only_tools": sorted(set(public["tool_names"]) - set(train["tool_names"])),
        }
    data = json.dumps(reports, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(data + "\n", encoding="utf-8")
    print(data)

if __name__ == "__main__":
    main()
