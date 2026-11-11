"""One custom JSON action objective, with verified prompt prefix and completion masks."""

import json
from typing import Protocol

from ..runtime.validation import parse_decision


class Tokenizer(Protocol):
    eos_token_id: int

    def apply_chat_template(self, messages: list[dict], **kwargs) -> str: ...
    def __call__(self, text: str, **kwargs) -> dict: ...
    def decode(self, ids: list[int], **kwargs) -> str: ...


def serialize_action(action: dict | str) -> str:
    return json.dumps(
        parse_decision(action), ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def tokenized_example(row: dict, tokenizer: Tokenizer, max_length: int) -> dict[str, list[int]]:
    messages = row["messages"]
    if [m["role"] for m in messages] != ["system", "user", "assistant"]:
        raise ValueError("Expected action-context system/user plus one assistant target")
    target = serialize_action(messages[-1]["content"])
    if "target" in row and serialize_action(row["target"]) != target:
        raise ValueError("Trajectory target/messages mismatch")
    prompt = tokenizer.apply_chat_template(
        messages[:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False
    )

    def encode(text):
        encoded = tokenizer(text, add_special_tokens=False)
        return list(encoded["input_ids"])

    prefix = encode(prompt)
    full = encode(prompt + target)
    if not prefix or full[: len(prefix)] != prefix:
        raise ValueError("Tokenizer boundary/template prefix mismatch")
    if len(full) <= len(prefix):
        raise ValueError("Empty action target tokens")
    eos = tokenizer.eos_token_id
    if type(eos) is not int:
        raise ValueError("Tokenizer must declare integer EOS")
    ids = full + [eos]
    if len(ids) > max_length:
        raise ValueError("CONTEXT_OVERFLOW: training example cannot be truncated")
    if tokenizer.decode(full[len(prefix) :], skip_special_tokens=False) != target:
        raise ValueError("Action token roundtrip mismatch")
    return {
        "input_ids": ids,
        "attention_mask": [1] * len(ids),
        "labels": [-100] * len(prefix) + ids[len(prefix) :],
    }


class ActionCollator:
    def __init__(self, pad_token_id, *, tensor=False):
        self.pad_token_id = pad_token_id
        self.tensor = tensor

    def __call__(self, rows):
        if not rows:
            raise ValueError("Empty training batch")
        width = max(len(row["input_ids"]) for row in rows)
        batch: dict[str, list[list[int]]] = {"input_ids": [], "attention_mask": [], "labels": []}
        for row in rows:
            n = len(row["input_ids"])
            padding = width - n
            if (
                len(row["labels"]) != n
                or len(row["attention_mask"]) != n
                or not any(x != -100 for x in row["labels"])
            ):
                raise ValueError("Invalid supervised action mask")
            batch["input_ids"].append(row["input_ids"] + [self.pad_token_id] * padding)
            batch["attention_mask"].append(row["attention_mask"] + [0] * padding)
            batch["labels"].append(row["labels"] + [-100] * padding)
        if self.tensor:
            import torch  # type: ignore[import-not-found,import-untyped]

            return {k: torch.tensor(v, dtype=torch.long) for k, v in batch.items()}
        return batch
