"""Publish checkpoints and final output for a single prediction run."""

from __future__ import annotations

import platform
from collections.abc import Iterable
from pathlib import Path

from .artifacts import external_output, save_json, write_jsonl
from .contracts import Payload, RunMetadata
from .submission import write_submission


class PredictionArtifacts:
    """Own the files and publication order for one prediction run."""

    def __init__(self, out: Path, *, inputs: Iterable[Path | None]) -> None:
        inputs = tuple(inputs)
        self.output = external_output(out, inputs=inputs)
        self._run_path = self.output.with_suffix(".run.json")
        self._diagnostics_path = self.output.with_suffix(".diagnostics.json")
        self._partial_path = self.output.with_suffix(".partial.jsonl")
        checked = [self.output]
        for path in (self._run_path, self._diagnostics_path, self._partial_path):
            external_output(path, inputs=inputs, outputs=checked)
            checked.append(path)
        self._metadata: RunMetadata
        self._predictions: list[Payload] = []
        self._diagnostics: list[Payload] = []
        self._diagnostics_written = False

    def start(self, metadata: RunMetadata) -> None:
        # Reserve the destination for this run before starting any backend.
        save_json(self._run_path, metadata.model_dump())
        self._metadata = metadata

    def record_model(self, model: Payload) -> None:
        self._metadata.model = model
        self._save_metadata()

    def record_sample(
        self, sample_id: str, prediction: Payload, diagnostic: Payload, *, setup_seconds: float
    ) -> None:
        self._predictions.append(prediction)
        write_jsonl(
            self._partial_path, self._predictions, replace=bool(self._metadata.completed_ids)
        )
        self._metadata.completed_ids.append(sample_id)
        self._diagnostics.append(diagnostic)
        self._save_diagnostics(
            {"backend_setup_seconds": setup_seconds, "python_version": platform.python_version()}
        )
        self._save_metadata()

    def complete(self) -> dict:
        write_submission(self._predictions, self._metadata.selected_ids, self.output)
        self._metadata.status = "COMPLETE"
        self._save_metadata()
        return {
            "status": self._metadata.status,
            "samples": len(self._predictions),
            "output": str(self.output),
            "identities": self._metadata.identities,
        }

    def fail(self, error: BaseException) -> None:
        if self._metadata.status == "COMPLETE":
            return  # The final submission was already published.
        diagnostic = getattr(error, "diagnostic", None)
        if diagnostic is not None:
            self._diagnostics.append(
                {
                    key: diagnostic[key]
                    for key in ("id", "stop_reason", "tool_calls", "state_hash")
                    if key in diagnostic
                }
            )
        self._metadata.status = "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "FAILED"
        self._metadata.error_type = type(error).__name__
        try:
            self._save_diagnostics({"failed_error_type": self._metadata.error_type})
        finally:
            self._save_metadata()

    def _save_metadata(self) -> None:
        save_json(self._run_path, self._metadata.model_dump(), replace=True)

    def _save_diagnostics(self, details: Payload) -> None:
        save_json(
            self._diagnostics_path,
            {**details, "records": self._diagnostics},
            replace=self._diagnostics_written,
        )
        self._diagnostics_written = True
