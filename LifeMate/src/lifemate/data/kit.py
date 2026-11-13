"""Read split-specific manifests and expose only inference fields to the agent."""

from pathlib import Path, PureWindowsPath

from ..contracts import InferenceSample, ToolSpec, json_object
from .splits import frozen_split as frozen_split

SPLITS = ("train", "public_test", "private_test")
ASK = "sys.ask_missing_info"


def resolve_data_root(root):
    root = Path(root).resolve()

    def contains_split(path):
        return any((path / split / f"{split}_tools_catalog.json").is_file() for split in SPLITS)

    if contains_split(root):
        return root
    matches = [path for path in root.iterdir() if path.is_dir() and contains_split(path)]
    if len(matches) > 1:
        raise ValueError(f"Multiple organizer kit roots under {root}")
    if not matches:
        raise FileNotFoundError(f"No organizer split catalog under {root}")
    return matches[0].resolve()


def split_dir(root, split):
    if split not in SPLITS:
        raise ValueError(f"Unknown organizer split: {split}")
    return resolve_data_root(root) / split


def read_jsonl(path):
    rows = []
    seen = set()
    with Path(path).open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json_object(line)
                sample_id = row.get("id")
                if not isinstance(sample_id, str) or not sample_id.strip():
                    raise ValueError("Expected a nonempty string ID")
                if sample_id in seen:
                    raise ValueError("Duplicate ID")
            except ValueError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
            seen.add(sample_id)
            rows.append(row)
    return rows


def load_manifest(root, split):
    rows = read_jsonl(split_dir(root, split) / f"{split}.jsonl")
    for row in rows:
        sample_id = row["id"]
        if (
            sample_id in {".", ".."}
            or PureWindowsPath(sample_id).name != sample_id
            or any(c in sample_id for c in "/\\:\x00")
        ):
            raise ValueError("Manifest ID must be a single path component")
    return rows


def load_catalog(root, split):
    path = split_dir(root, split) / f"{split}_tools_catalog.json"
    data = json_object(path.read_text(encoding="utf-8"))
    tools = {}
    for app in data["apps"]:
        for tool in app["tools"]:
            spec = ToolSpec.model_validate(tool)
            if spec.app != app["id"] or not spec.name.startswith(spec.app + "."):
                raise ValueError(f"Invalid tool association in {path}")
            if spec.name in tools:
                raise ValueError(f"Duplicate tool {spec.name} in {path}")
            tools[spec.name] = spec.model_dump(exclude_unset=True)
    return tools


def allowed_tools(sample, catalog):
    installed = sample.get("context", {}).get("installed_apps", {})
    registry = {}
    for app, settings in installed.items():
        names = settings.get("tools")
        if not isinstance(names, list):
            raise ValueError(f"Expected installed tool list for {app}")
        for name in names:
            if not isinstance(name, str) or name not in catalog or catalog[name]["app"] != app:
                raise ValueError(f"Tool does not belong to installed app {app}")
            registry[name] = catalog[name]
    if ASK in catalog:
        registry[ASK] = catalog[ASK]
    return registry


def inference_input(row, *, oracle_text=False, split="train"):
    if oracle_text and split != "train":
        raise ValueError("Oracle transcripts are train-only")
    sample = {key: row[key] for key in ("id", "audio", "context") if key in row}
    if oracle_text:
        sample["text"] = row["audio_text"]
    history = []
    for turn in row.get("history", []):
        if turn["role"] == "user":
            visible = {key: turn[key] for key in ("role", "audio") if key in turn}
            if oracle_text and "audio_text" in turn:
                visible["text"] = turn["audio_text"]
        else:
            visible = {
                key: turn[key]
                for key in ("role", "text", "tool_calls", "tool_results")
                if key in turn
            }
        history.append(visible)
    sample["history"] = history
    return InferenceSample.model_validate(sample).model_dump(exclude_unset=True, exclude_none=True)
