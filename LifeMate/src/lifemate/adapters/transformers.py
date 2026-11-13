"""Optional local Transformers backend. No model downloads or remote services."""

import os
import time
from pathlib import Path


class LocalPolicy:
    def __init__(
        self,
        model_path,
        max_context_tokens=16384,
        max_new_tokens=512,
        *,
        tokenizer_path=None,
        adapter_path=None,
    ):
        path = Path(model_path).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Local model directory missing: {path}")
        if max_new_tokens < 1 or max_context_tokens <= max_new_tokens:
            raise ValueError("Context budget must exceed positive generation budget")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        try:
            import torch  # type: ignore[import-not-found,import-untyped]
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore[import-not-found,import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "Install the optional model dependencies and provide local weights"
            ) from exc
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            Path(tokenizer_path or path), local_files_only=True, trust_remote_code=False
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            path,
            local_files_only=True,
            trust_remote_code=False,
            device_map="auto",
            dtype="auto",
        ).eval()
        if adapter_path is not None:
            from peft import PeftModel  # type: ignore[import-not-found,import-untyped]

            adapter_path = Path(adapter_path).resolve()
            if not adapter_path.is_dir():
                raise FileNotFoundError("Local adapter directory missing")
            self.model = PeftModel.from_pretrained(
                self.model, adapter_path, local_files_only=True
            ).eval()
        self.metadata = {
            "backend": "transformers",
            "model_path": str(path),
            "tokenizer_path": str(tokenizer_path or path),
            "adapter_path": str(adapter_path) if adapter_path else None,
        }
        self.max_context_tokens = max_context_tokens
        self.max_new_tokens = max_new_tokens
        self.last_usage = {}

    def next_action(self, messages: list[dict[str, str]], *, deadline: float) -> str:
        from transformers import StoppingCriteria, StoppingCriteriaList  # type: ignore[import-not-found,import-untyped]

        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.monotonic() >= deadline

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        count = inputs["input_ids"].shape[-1]
        if count + self.max_new_tokens > self.max_context_tokens:
            raise ValueError("Full eligible schema/history exceeds configured context budget")
        if time.monotonic() >= deadline:
            raise TimeoutError("Sample deadline reached before generation")
        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                num_beams=1,
                stopping_criteria=StoppingCriteriaList([Deadline()]),
                pad_token_id=self.tokenizer.eos_token_id,
            )
        self.last_usage = {"prompt_tokens": count, "generated_tokens": output.shape[-1] - count}
        if time.monotonic() >= deadline:
            raise TimeoutError("Transformers response exceeded deadline")
        return self.tokenizer.decode(output[0, count:], skip_special_tokens=True).strip()

    def plan(self, request_context, *, deadline):
        from ..runtime.goals import PolicyPlanner

        return PolicyPlanner(self).plan(request_context, deadline=deadline)

    def bind(self, request_context, *, deadline):
        import json

        from ..contracts import json_loads

        raw = self.next_action(
            [
                {
                    "role": "system",
                    "content": 'Bind this proposed action to exactly one explicitly requested pending occurrence. Return only {"occurrence_id":"id"}. Choose only when intent and span support it; otherwise return {"occurrence_id":null}. No tool call is executed by this binding.',
                },
                {"role": "user", "content": json.dumps(request_context, ensure_ascii=False)},
            ],
            deadline=deadline,
        )
        value = json_loads(raw)
        if (
            not isinstance(value, dict)
            or set(value) != {"occurrence_id"}
            or not isinstance(value["occurrence_id"], str)
        ):
            from ..runtime.validation import Rejected

            raise Rejected("Ambiguous goal occurrence binding")
        return value["occurrence_id"]
