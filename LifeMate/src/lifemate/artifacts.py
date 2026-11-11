"""Path ownership and atomic publication. Runtime artifacts belong outside source."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PACKAGE_ROOT.parent.parent if PACKAGE_ROOT.parent.name == "src" else PACKAGE_ROOT


def overlaps(a, b):
    a, b = Path(a).resolve(), Path(b).resolve()
    return a == b or a in b.parents or b in a.parents


def external_output(path, *, inputs=(), outputs=(), source_root=None, refuse_existing=True):
    path = Path(path).resolve()
    protected = [
        PACKAGE_ROOT.resolve(),
        Path(source_root or SOURCE_ROOT).resolve(),
        *[Path(p).resolve() for p in inputs if p is not None],
    ]
    checkout = Path.cwd().resolve()
    if (checkout / "pyproject.toml").is_file() and (checkout / "src/lifemate").is_dir():
        protected.append(checkout)
    if any(overlaps(path, p) for p in protected):
        raise ValueError(f"Output overlaps source/protected input: {path}")
    if any(overlaps(path, p) for p in outputs):
        raise ValueError(f"Output collision: {path}")
    if refuse_existing and path.exists():
        raise FileExistsError(f"Output exists; select a new run destination: {path}")
    return path


def audio_path(root, value):
    lexical = Path(root).absolute()
    parent = lexical.parent.resolve()
    root = lexical.resolve()

    def protected(parts):
        return any(
            p.lower() in {"env", "environment", "environments", "states"}
            or p.lower().endswith("_environment")
            for p in parts
        )

    if not root.is_relative_to(parent) or protected(root.parts):
        raise ValueError("Audio root resolves outside selected split or into environment state")
    path = (root / value).resolve()
    if not path.is_relative_to(root) or protected(path.parts):
        raise ValueError("Audio path escapes authorized audio root")
    if path.suffix.lower() != ".wav" or not path.is_file():
        raise ValueError("Missing/unsupported WAV input")
    return path


def atomic_text(path, content, *, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(f"Output exists: {path}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix="." + path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # Hard-link is an atomic no-clobber publish on supported local filesystems.
            if os.name == "nt":
                os.rename(
                    temporary, path
                )  # Windows rename is atomic and refuses an existing target.
            else:
                os.link(temporary, path)
                temporary.unlink()
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_json(path, value, *, replace=False):
    atomic_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        replace=replace,
    )


def write_jsonl(path, rows, *, replace=False):
    content = "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows)
    atomic_text(path, content, replace=replace)
