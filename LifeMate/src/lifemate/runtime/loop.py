"""One official session; bounded proposals and evidence-backed goal occurrences."""

from __future__ import annotations

import copy
import json
import time
from collections.abc import Callable
from pathlib import Path

from ..adapters.protocols import Clock, GoalPlanner, Policy, Session
from ..adapters.sdk import open_env
from ..config import RunConfig as RunConfig
from ..contracts import DiagnosticRecord, InferenceSample, SubmissionRow
from ..data.kit import allowed_tools
from .context import compile_messages
from .goals import Ledger, PolicyPlanner
from .normalize import normalize
from .outcomes import classify
from .references import ReferenceIndex
from .validation import Rejected, checked_call, parse_decision


class SampleFailure(RuntimeError):
    diagnostic: dict


def infer(
    sample: dict,
    root: str | Path,
    split: str,
    catalog: dict,
    policy: Policy,
    config: RunConfig | None = None,
    *,
    env_factory: Callable[..., Session] = open_env,
    planner: GoalPlanner | None = None,
    clock: Clock = time,
    prepare: Callable[[dict, float], dict] | None = None,
) -> tuple[dict, dict]:
    config = config or RunConfig()
    sample = InferenceSample.model_validate(sample).model_dump(
        exclude_none=True, exclude_unset=True
    )
    started = clock.monotonic()
    deadline = started + config.sample_seconds
    registry = allowed_tools(sample, catalog)
    # Construction failure is fatal; never fabricate a hash or reconstruct a session.
    env = env_factory(root, split, sample["id"])
    sdk_seconds = float(clock.monotonic() - started)
    timing = {
        "sdk_seconds": sdk_seconds,
        "planning_seconds": 0.0,
        "policy_seconds": 0.0,
        "tool_seconds": 0.0,
        "asr_seconds": 0.0,
    }
    asr_diagnostics = []
    observations: list[dict] = []
    diagnostics: list[dict] = []
    repairs = 0
    generations = 0
    reconsidered = 0
    reason = "DECISION_CAP"
    ledger = None

    def on_time():
        if clock.monotonic() >= deadline:
            raise TimeoutError("Sample deadline reached")

    def generation():
        nonlocal generations
        on_time()
        if generations >= config.max_generations:
            raise Rejected("Generation cap reached")
        generations += 1

    try:
        on_time()
        if prepare is not None:
            sample = prepare(sample, deadline)
        asr_diagnostics = sample.pop("_asr_diagnostics", [])
        timing["asr_seconds"] = sum(item["elapsed_seconds"] for item in asr_diagnostics)
        if not isinstance(sample.get("text"), str):
            raise ValueError("Missing latest request transcript")
        sample["normalization"] = normalize(sample["text"], sample.get("context", {}))
        references = ReferenceIndex(sample)
        request = json.loads(compile_messages(sample, registry, [])[1]["content"])
        plan_error = None
        for _attempt in range(config.max_repairs + 1):
            generation()
            try:
                actual_planner = planner or (
                    policy if hasattr(policy, "plan") else PolicyPlanner(policy)
                )
                planning_started = clock.monotonic()
                plan = actual_planner.plan(
                    {**request, "planning_rejection": plan_error}, deadline=deadline
                )
                timing["planning_seconds"] += clock.monotonic() - planning_started
                on_time()
                ledger = Ledger(plan, sample["text"], registry)
                break
            except (ValueError, Rejected) as exc:
                plan_error = type(exc).__name__ + ": " + str(exc)
                diagnostics.append({"planning_rejection": plan_error})
        if ledger is None:
            raise Rejected("Goal planning unresolved")
        rejection = None
        for step in range(config.max_decisions):
            generation()
            messages = compile_messages(
                sample, registry, observations, rejection, ledger=ledger.dump()
            )
            entry: dict = {"step": step}
            diagnostics.append(entry)
            try:
                policy_started = clock.monotonic()
                proposed = policy.next_action(messages, deadline=deadline)
                timing["policy_seconds"] += clock.monotonic() - policy_started
                try:
                    json.dumps(proposed, allow_nan=False)
                    entry["proposal"] = proposed
                except (ValueError, TypeError):
                    entry["proposal"] = {"invalid_type": type(proposed).__name__}
                entry["usage"] = copy.deepcopy(getattr(policy, "last_usage", {}))
                on_time()
                decision = parse_decision(proposed)
                if decision["kind"] == "DONE":
                    pending = ledger.pending(observations)
                    if pending and reconsidered < config.done_reconsiderations:
                        reconsidered += 1
                        rejection = "Premature DONE; pending goal occurrences: " + str(pending)
                        entry["rejection"] = rejection
                        continue
                    reason = (
                        ("BUSINESS_NOOP" if ledger.noops else "PREMATURE_DONE")
                        if pending
                        else "DONE"
                    )
                    break

                # All project semantic guards precede the final SDK validation.
                class Guard:
                    def validate(self, name, args):
                        return {"ok": True}

                name, args = checked_call(decision, registry, Guard())
                entry["reference_provenance"] = references.check(
                    args, registry[name]["parameters"], name
                )
                bound = None
                if registry[name]["kind"] == "write":
                    candidates = ledger.candidates(name, args, observations)
                    choice = None
                    if len(candidates) > 1 and hasattr(policy, "bind"):
                        generation()
                        choice = policy.bind(
                            {
                                "action": {"name": name, "arguments": args},
                                "candidates": [
                                    {"goal": g.model_dump(), "occurrence": o.id}
                                    for g, o in candidates
                                ],
                                "latest_user_text": sample["text"],
                            },
                            deadline=deadline,
                        )
                        on_time()
                    bound = ledger.bind(name, args, observations, choice)
                checked = env.validate(name, args)
                if checked.get("ok") is not True:
                    raise Rejected("SDK validation rejected proposal")
            except Rejected as exc:
                entry["rejection"] = str(exc)
                rejection = str(exc)
                repairs += 1
                if repairs > config.max_repairs:
                    reason = "BUSINESS_NOOP" if ledger.noops else "VALIDATION_REJECTION"
                    break
                continue
            rejection = None
            on_time()
            tool_started = clock.monotonic()
            result = env.call(name, args)
            timing["tool_seconds"] += clock.monotonic() - tool_started
            outcome = classify(registry[name]["kind"], result, name)
            observed = {
                "name": name,
                "arguments": copy.deepcopy(args),
                "result": copy.deepcopy(result),
                "outcome": outcome,
            }
            observations.append(observed)
            references.observe(name, result, f"live:{len(observations) - 1}", args)
            entry["observation"] = observed
            if bound:
                ledger.record(bound[0], bound[1], outcome, args, len(observations) - 1)
            elif registry[name]["kind"] == "read":
                candidates = ledger.candidates(name, args, observations)
                if len(candidates) == 1:
                    ledger.record(
                        candidates[0][0], candidates[0][1], outcome, args, len(observations) - 1
                    )
            if decision["kind"] == "ASK":
                reason = "ASK"
                break
            if outcome in ("UNKNOWN", "SCHEMA_REJECTED") and registry[name]["kind"] == "write":
                reason = outcome
                break
            # Proven no-effect remains pending; only corrective reads/new args can recover.
        else:
            reason = "DECISION_CAP"
    except TimeoutError:
        reason = "TIMEOUT"
        diagnostics.append({"error_type": "TimeoutError"})
    except Rejected as exc:
        reason = "BLOCKED"
        diagnostics.append({"error_type": type(exc).__name__, "error": str(exc)})
    except Exception as exc:
        reason = "CONTEXT_OVERFLOW" if "CONTEXT_OVERFLOW" in str(exc) else "RUNTIME_ERROR"
        diagnostics.append({"error_type": type(exc).__name__})
        # Fatal transcription/context/runtime errors must not publish a complete submission.
        error = SampleFailure(reason)
        error.diagnostic = {
            "id": sample["id"],
            "stop_reason": reason,
            "tool_calls": env.get_tool_calls(),
            "state_hash": env.get_state_hash(),
        }
        raise error from exc
    prediction = {
        "id": sample["id"],
        "tool_calls": env.get_tool_calls(),
        "state_hash": env.get_state_hash(),
    }
    SubmissionRow.model_validate(prediction)
    json.dumps(prediction, ensure_ascii=False, allow_nan=False)
    diagnostic = {
        "id": sample["id"],
        "stop_reason": reason,
        "elapsed_seconds": float(clock.monotonic() - started),
        "steps": diagnostics,
        "goals": ledger.dump() if ledger else [],
        "generations": generations,
        "timing": timing,
        "transcriptions": asr_diagnostics,
    }
    return prediction, DiagnosticRecord.model_validate(diagnostic).model_dump()
