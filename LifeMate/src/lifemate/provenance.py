"""Ordered recursive path/length/digest identities, separate from SDK state hashes."""

import hashlib
import json
from pathlib import Path


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root, paths):
    root = Path(root).resolve()
    return [
        {
            "path": Path(p).resolve().relative_to(root).as_posix(),
            "length": Path(p).stat().st_size,
            "sha256": file_sha256(p),
        }
        for p in sorted(paths, key=lambda p: Path(p).as_posix())
    ]


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def source_identity(root=None, *, package_root=None):
    package = Path(package_root or Path(__file__).resolve().parent).resolve()
    if root is None:
        # Editable checkout and a normally installed wheel have different layouts.
        root = package.parent.parent if package.parent.name == "src" else package.parent
        source = package
    else:
        root = Path(root).resolve()
        source = root / "src/lifemate"
    root = Path(root).resolve()
    paths = list(source.rglob("*.py"))
    if (source / "py.typed").is_file():
        paths.append(source / "py.typed")
    if source.parent.name == "src":
        paths += list((root / "configs").glob("*.json"))
        paths += list((root / "scripts").glob("*.py")) + list((root / "scripts").glob("*.ps1"))
        paths += [
            root / p
            for p in ("pyproject.toml", "MANIFEST.in", "Dockerfile", ".dockerignore", "predict.sh")
            if (root / p).is_file()
        ]
    if not paths:
        raise ValueError("No owned Python source available for provenance")
    return digest(manifest(root, paths))
