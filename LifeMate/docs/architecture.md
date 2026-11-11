# Architecture

LifeMate implements C01-C15 as offline application software. Controlled fixtures
prove enforcement for supplied decisions and observations, not learned semantic
accuracy, training success, official scorer parity or release compliance.

Dependencies flow from contracts/configuration through data/runtime/learning/metrics,
adapters, workflows and CLI. `contracts.py` supplies strict Pydantic records; dynamic
catalog schemas retain descriptions, nested structure and extensions. JSON rejects
duplicate keys, nonfinite tokens and overflow-to-infinity. Config paths resolve beside
the JSON file; supplied CLI flags resolve from the invoking directory.

`data/kit.py` resolves direct known split paths or one wrapper without reading hidden
state. Selected assets must be complete; no train fallback is used. The inference
projection excludes labels/final state/future targets; oracle text is train-only.
`data/splits.py` validates exact scenario coverage, uniqueness, source bytes digest,
disjoint partitions and held-out app exposure before selection/expansion.

`runtime/context.py` retains sample-local clock/timezone/profile/location, chronological
history, previous tool results, all eligible schemas and actual observations. History
operations are already applied and never replayed. This serializer also creates
teacher-forced action context; preparation never derives a goal plan from future gold
effects. Required schemas/evidence are not pruned to fit. Tool/catalog content is input
evidence, not authority to expand capabilities.

`runtime/normalize.py` emits raw text, supported span values, supersession, negation and
uncertainty instead of rewriting phone strings/text/optional values. Money units,
half-hour/kém, relative offsets, next-calendar-week weekdays and dates use sample time.
`references.py` records explicit/history/live evidence with collection and available
type/parent attributes. Invented IDs and known collection/device/menu-parent mismatch
block writes. Provenance does not prove current existence or select the first of
multiple lookup results; a permitted read/ASK resolves remaining uncertainty.

`runtime/goals.py` validates eligible tools, unique request-backed occurrence spans,
acyclic dependencies and no planner effect/status claims. Planning and binding are
separate internal local JSON prompts, never official tools. Each mutation binds to a
pending compatible occurrence; ambiguous equal requests require an explicit internal
binding. Actual compatible effects alone complete writes. Conditions use actual read
fields and type-sensitive comparisons. Completed writes cannot repeat; uncertain
outcomes quarantine the occurrence. Explicit distinct occurrences may repeat equal
arguments once each. No-op recovery is narrow: inspected banking no-effect messages,
new matching account/beneficiary read evidence, unchanged amount/other effect arguments,
sufficient observed balance, and a two-attempt cap. Unproven cause linkage blocks retry.
Actual planner/binder language understanding remains an experiment.

`runtime/loop.py` constructs exactly one selected official session and checks clock
before planning/generation/repair/binding and each real call. Order: parse, project
scope/schema/reference/goal checks, official validate, deadline, call, actual observation.
DONE stays internal and gets at most one reconsideration for pending goals; ASK maps
to real sys.ask_missing_info with target/params and ends the turn. Invalid proposals
never log; actual failed attempts remain forever. Inference has no state getter.
SDK initialization/getter failure is fatal, with no fabricated hash. Fatal sample
diagnostics preserve real trace/hash when usable; no final submission publishes.
Timeout/cap with usable getters preserves actual values and explicit stop reason.
SDK construction and GPU kernels are not forcibly preempted.

Local Ollama/Transformers/Whisper adapters import heavy libraries only on request.
ASR handles latest and history user WAVs in chronological association, with mono
conversion and explicit resampling. Current support is mono/stereo PCM, rate >=8000
Hz, **at most 30 seconds per WAV**. Longer audio fails explicitly; no silent short-form
truncation or oracle fallback. Diagnostics measure per-turn ASR and aggregate SDK,
planning, policy and tool times; backend setup is separate. Unmeasured quality/hardware
facts remain unmeasured.

`learning/trajectories.py` checks each actual teacher-forced result before accepting
rows. READ/WRITE/ASK and terminal DONE share inference action JSON; ASK still receives
training DONE, and zero-call scenarios produce immediate DONE. `serialization.py`
checks exact tokenizer prompt prefix and action roundtrip. Prompt/history/observations/
previous actions and padding have label -100; only the current action plus EOS is
supervised. Oversize/template mismatch fails without truncation. `trainer.py` contains
real lazy TRL/PEFT train/save integration and injectable tests; preparation/dry-run
never starts it. See [local_training.md](local_training.md).

`metrics/` preserves maximum one-to-one PROXY matching and independent hash/call
accuracy, first/later/whole trajectory, confusion/slices and compatible paired reports.
Supplied ASR artifacts yield WER/CER denominators and critical-slot/downstream deltas
without launching models. `artifacts.py` protects source/inputs and flushes unique
sibling temporary writes before atomic publication. `prediction_artifacts.py` owns
the prediction sidecars and records completed IDs after their checkpoint is written.
It publishes the final submission only when all selected IDs pass. Incomplete
checkpoints and metadata never reconstruct a session. `provenance.py` hashes nested
owned source and configured inputs separately
from the SDK state hash. Legacy files remain explicit compatibility facades. New public
workflow/runtime/learning interfaces are typed and validate dynamic JSON at entry.
