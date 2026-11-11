#!/usr/bin/env python3
"""Prepare a small LifeMate SDK/docs review bundle from a local organizer ZIP.

Copies documentation, non-data tool catalogs, and Python SDK/scorer code only.
Does NOT copy audio, scenario records, raw app state, labels or answer files.
Run only if sharing the selected files is permitted by the organizer's terms.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

DEFAULT_CAP_MB = 40
PER_FILE_CAP_MB = 10


def allow(path: str) -> bool:
    p = PurePosixPath(path.replace('\\', '/'))
    parts = [s.lower() for s in p.parts]
    name = p.name.lower()
    if not name or name.startswith('.') or any(s in ('__macosx', '.git', 'audio', 'audios', 'models', 'checkpoints', 'weights') for s in parts):
        return False
    # Explicitly reject all scenario-specific files and personal/source app data.
    if any(s.endswith('_environment') or s == 'state.json' or s.endswith('_environment') for s in parts):
        return False
    if any(s in ('environment', 'environments') for s in parts):
        return False
    if any(re.match(r'(?:train|public|private|test)_[0-9a-z-]+$', s) for s in parts):
        return False
    if name in ('train.jsonl', 'public_test.jsonl', 'private_test.jsonl', 'sample_submission.jsonl', 'submission.jsonl'):
        return False
    if name.endswith(('.wav', '.mp3', '.flac', '.ogg', '.m4a', '.safetensors', '.pt', '.bin', '.pkl', '.sqlite', '.db', '.jsonl', '.csv')):
        return False
    if name in ('readme.md', 'readme.txt', 'version', 'rules.md', 'evaluation.md', 'submission.md', 'submission_guidance.md', 'requirements.txt'):
        return True
    if name.endswith('_tools_catalog.json'):
        return True
    if name.endswith('.py') and (
        'zaic_tools' in parts or any(key in name for key in ('eval', 'score', 'validator', 'check', 'toolenv', 'tool_env'))
    ):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path, help='Path to original train+public_test.zip')
    ap.add_argument('--out', type=Path, default=Path('LifeMate_Kit_Review_Small.zip'))
    ap.add_argument('--max-mb', type=int, default=DEFAULT_CAP_MB)
    args = ap.parse_args()
    if not args.archive.is_file():
        ap.error(f'ZIP not found: {args.archive}')
    total_cap = args.max_mb * 1024 * 1024
    individual_cap = PER_FILE_CAP_MB * 1024 * 1024
    selected = []
    skipped_oversize = []
    total = 0

    with zipfile.ZipFile(args.archive) as src:
        for info in src.infolist():
            if info.is_dir() or not allow(info.filename):
                continue
            if info.file_size > individual_cap or total + info.file_size > total_cap:
                skipped_oversize.append({'path': info.filename, 'size': info.file_size})
                continue
            # Verify filenames cannot traverse paths or be absolute.
            path = PurePosixPath(info.filename.replace('\\', '/'))
            if path.is_absolute() or '..' in path.parts:
                continue
            selected.append(info)
            total += info.file_size

        if not selected:
            print('No matching review files found. Check the ZIP structure or filenames.', file=sys.stderr)
            return 2

        report = {
            'origin': args.archive.name,
            'purpose': 'SDK and schema review only; excludes scenario data',
            'selected_file_count': len(selected),
            'selected_total_uncompressed_bytes': total,
            'selected': [{'path': i.filename, 'size_bytes': i.file_size} for i in selected],
            'skipped_oversize': skipped_oversize,
            'note': 'Review organizer terms before sharing; some SDK/catalog materials may be restricted.'
        }
        with zipfile.ZipFile(args.out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as dst:
            dst.writestr('review_manifest.json', json.dumps(report, indent=2, ensure_ascii=False))
            for info in selected:
                # Stream each selected source member without extracting the large archive.
                with src.open(info) as infile, dst.open(info.filename, 'w', force_zip64=True) as outfile:
                    while True:
                        chunk = infile.read(1024 * 1024)
                        if not chunk:
                            break
                        outfile.write(chunk)
    print(f'Created {args.out.resolve()} ({args.out.stat().st_size:,} bytes, {len(selected)} files)')
    print('Before uploading, check review_manifest.json and confirm sharing is allowed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
