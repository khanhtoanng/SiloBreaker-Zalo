"""Load the selected external SDK under a unique name to avoid cross-split imports."""

from __future__ import annotations

import hashlib
import importlib.util
import sys

from ..data.kit import resolve_data_root, split_dir


def load_sdk(root, split):
    directory = split_dir(root, split) / "zaic_tools"
    path = directory / "__init__.py"
    if not path.is_file():
        raise FileNotFoundError(f"Missing official {split} SDK: {path}")
    name = "_lifemate_sdk_" + hashlib.sha256(str(directory).encode()).hexdigest()[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, path, submodule_search_locations=[str(directory)]
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load official SDK: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            for key in list(sys.modules):
                if key == name or key.startswith(name + "."):
                    del sys.modules[key]
            raise
    return sys.modules[name]


def open_env(root, split, sample_id):
    root = resolve_data_root(root)
    return load_sdk(root, split).ToolEnv(split, sample_id, root=root)
