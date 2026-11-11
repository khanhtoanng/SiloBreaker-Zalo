# Edge-case software evidence

All checks use authored synthetic inputs. SDK means the actual external train/public
SDK Session on authored state dictionaries, with no real-data ToolEnv or direct
state-file access. CORE/POLICY fixtures prove enforcement for controlled plans,
decisions and observations, not learned decomposition/semantic accuracy or hidden
gold conventions. PROXY/SCORER denotes explicitly unverified official scoring.

Final observed suite status and exact command/exit code are in the revision-bound
implementation evidence. Each named check below is required in that suite; skipped
SDK checks count as NOT VERIFIED, never PASS. Real train replay, frozen end-to-end
baseline, actual ASR/tokenizer/forward-loss/training, hardware and Docker are NOT RUN.

## P0 pre-training gate

Retain K01-K13, K18, K25-K30, K35-K38, K45-K48 and K53 as the original mandatory
software gate. A fixture pass does not authorize training: inspect current software
results, actual authorized replay, frozen baseline and real tokenizer/loss proof
before a later separately authorized training job. The rest stays visible for
pre-release POLICY/SDK/SCORER checks and paired holdout regression measurement.

| Case | Named executable check(s) | Evidence kind | Covered behavior / deferred limit |
|---|---|---|---|
| K01 | `test_runtime.RuntimeTests.test_K01_uninstalled_tool_blocked` | CORE | Installed scope |
| K02 | `test_runtime.RuntimeTests.test_K02_required_blocked_before_sdk_call; test_sdk_contract.SDKContracts.test_K02_validate_does_not_log_or_mutate` | CORE+SDK | Required validation is log-free |
| K03 | `test_runtime.SchemaTests.test_K03_enum` | CORE | Strict enum |
| K04 | `test_runtime.SchemaTests.test_K04_K38_integer_types_and_range` | CORE | No amount coercion |
| K05 | `test_runtime.SchemaTests.test_K05_x_one_of` | CORE | Actual alternatives |
| K06 | `test_sdk_contract.SDKContracts.test_K06_xref_passes_schema_but_noops; test_references.ReferenceTests.test_schema_literal_grounding_and_filename_not_evidence` | CORE+SDK | Existence versus provenance |
| K07 | `test_sdk_contract.SDKContracts.test_K07_nested_gap_and_own_preflight` | CORE+SDK | Nested semantic guard |
| K08 | `test_runtime.SchemaTests.test_K08_extra_fields_rejected; test_validation.ValidationTests.test_nested_optional_present_wrong_types` | CORE | Unknown/explicit optional values |
| K09 | `test_sdk_contract.SDKContracts.test_K09_failed_attempt_is_logged` | SDK | True failed attempts remain |
| K10 | `test_runtime.RuntimeTests.test_K10_K11_exact_getters_and_one_session` | CORE | Only actual getters |
| K11 | `test_loop.LoopTests.test_factory_and_getter_failure_fatal; test_runtime.RuntimeTests.test_K10_K11_exact_getters_and_one_session` | CORE | One session no replacement hash |
| K12 | `test_runtime.RuntimeTests.test_K12_history_kept_without_replay` | CORE | History is not replayed |
| K13 | `test_sdk_contract.SDKContracts.test_K13_K54_distinct_split_imports_and_full_coverage` | SDK | Split-specific SDK/catalog |
| K14 | `test_references.ReferenceTests.test_K14_device_room_and_type_disambiguates; test_runtime.RuntimeTests.test_read_then_observation_grounded_write` | CORE | Typed read-to-write |
| K15 | `test_references.ReferenceTests.test_K15_K20_K23_K24_ambiguity_and_empty_reads` | CORE | Ambiguity blocked |
| K16 | `test_sdk_contract.SDKContracts.test_K16_scenes_require_unfiltered_status` | SDK | Scene read contract |
| K17 | `test_references.ReferenceTests.test_K17_beneficiary_missing_or_ambiguous` | CORE | No recipient guess |
| K18 | `test_sdk_contract.SDKContracts.test_K18_insufficient_balance; test_goals.GoalTests.test_cause_linked_bank_recovery_and_unrelated_read_negative` | CORE+SDK | No-op not effect; cause-linked retry only |
| K19 | `test_references.ReferenceTests.test_K19_device_type_and_collection_mismatch; test_sdk_contract.SDKContracts.test_K19_wrong_device_type_noops` | CORE+SDK | Device type mismatch |
| K20 | `test_references.ReferenceTests.test_K15_K20_K23_K24_ambiguity_and_empty_reads` | CORE | Zero/multiple not first-match authority |
| K21 | `test_sdk_contract.SDKContracts.test_K21_unique_phone_equivalence_and_ambiguous_preservation` | SDK | Unique phone resolution preserves argument |
| K22 | `test_runtime.SchemaTests.test_reference_provenance_read_history_literal_and_unknown` | CORE | History references retained |
| K23 | `test_references.ReferenceTests.test_K15_K20_K23_K24_ambiguity_and_empty_reads` | CORE | Empty read cannot resolve ID |
| K24 | `test_loop.LoopTests.test_no_goals_cannot_write_and_no_fabricated_reference` | CORE | No assumed ID after lookup |
| K25 | `test_sdk_contract.SDKContracts.test_K25_ask_required_and_hash; test_validation.ValidationTests.test_ask_target_and_real_shape` | CORE+SDK | Real ASK required fields/hash |
| K26 | `test_runtime.RuntimeTests.test_K26_wrong_ask_param_blocked` | CORE | Installed target/real parameter |
| K27 | `test_loop.LoopTests.test_unsupported_withdrawn_plan_real_empty_hash` | CORE | Controlled no-action unchanged hash |
| K28 | `test_loop.LoopTests.test_two_goals_independent_success_then_ask` | CORE | Independent work retained |
| K29 | `test_loop.LoopTests.test_premature_done_reconsideration_keeps_goal; test_goals.GoalTests.test_K29_dependency_not_completed_by_unrelated_read` | CORE | Pending/dependent goal ledger |
| K30 | `test_goals.GoalTests.test_K30_completed_write_not_repeated` | CORE | No retry after effect |
| K31 | `test_goals.GoalTests.test_K31_deliberate_identical_occurrences_and_ambiguous_binding; test_loop.LoopTests.test_explicit_repeats_can_execute_twice_success_not_three` | CORE | Explicit occurrences not equality dedup |
| K32 | `test_normalize.NormalizeTests.test_K40_correction_and_negation; test_loop.LoopTests.test_unsupported_withdrawn_plan_real_empty_hash` | CORE/POLICY | Raw/corrected evidence and controlled withdrawn plan |
| K33 | `test_loop.LoopTests.test_K33_ambiguous_read_then_terminal_ask` | CORE/POLICY | Ask after ambiguous safe read |
| K34 | `test_loop.LoopTests.test_conditional_write_only_after_observed_true; test_loop.LoopTests.test_repeated_done_stops_truthfully_pending` | CORE/POLICY | Actual condition or truthful pending stop |
| K35 | `test_sdk_contract.SDKContracts.test_K35_K36_schedule_boundaries` | SDK | Equal sample time is immediate |
| K36 | `test_sdk_contract.SDKContracts.test_K35_K36_schedule_boundaries` | SDK | Past sample time is immediate |
| K37 | `test_runtime.SchemaTests.test_K37_missing_vehicle` | CORE | No invented vehicle |
| K38 | `test_normalize.NormalizeTests.test_K38_K39_money_no_phone_rewrite; test_runtime.SchemaTests.test_K04_K38_integer_types_and_range` | CORE | Units and strict integer |
| K39 | `test_sdk_contract.SDKContracts.test_K39_K42_sdk_defaults_without_invented_arguments` | SDK | Event end left to actual SDK |
| K40 | `test_normalize.NormalizeTests.test_K35_K36_rollover_sample_not_host; test_normalize.NormalizeTests.test_words_without_half_next_calendar_week_and_source_spans; test_normalize.NormalizeTests.test_evening_and_relative_hours_do_not_emit_spurious_absolute_time` | CORE/POLICY | Sample clock rollover/correction/weekday/evening |
| K41 | `test_references.ReferenceTests.test_K41_actual_schema_missing_nested_ref_still_checks_parent` | CORE | Actual menu schema parent guard |
| K42 | `test_sdk_contract.SDKContracts.test_K39_K42_sdk_defaults_without_invented_arguments` | SDK | Payment remains omitted/cash default |
| K43 | `test_sdk_contract.SDKContracts.test_K43_climate_requires_mode` | CORE+SDK | Required climate mode |
| K44 | `test_asr_metrics.AsrMetricTests.test_same_ids_config_critical_slots_and_downstream_delta` | CORE; D | Supplied pairing only; real ASR critical-slot quality NOT RUN |
| K45 | `test_sdk_contract.SDKContracts.test_K45_K46_freetext_hash_collision; test_runtime.EvaluatorTests.test_K45_K46_hash_not_text_equality` | SDK+PROXY | Hash is not text matching |
| K46 | `test_sdk_contract.SDKContracts.test_K45_K46_freetext_hash_collision` | SDK+SCORER | Canonical excluded text; official score UNKNOWN |
| K47 | `test_sdk_contract.SDKContracts.test_K47_information_state_ignored_by_hash` | SDK+SCORER | Information state excluded; score UNKNOWN |
| K48 | `test_runtime.EvaluatorTests.test_K48_extra_read_penalty` | PROXY | Extra read retained/matching penalty |
| K49 | `test_sdk_contract.SDKContracts.test_K49_array_order_contract` | SDK | Scalar/object order contract |
| K50 | `test_runtime.EvaluatorTests.test_fuzzy_strict_boundary` | PROXY+SCORER | Official fuzzy matching UNKNOWN |
| K51 | `test_runtime.EvaluatorTests.test_unordered_calls; test_runtime.RuntimeTests.test_read_then_observation_grounded_write` | PROXY+CORE | Proxy unordered matching versus causal execution |
| K52 | `test_sdk_contract.SDKContracts.test_K52_failed_then_correct_attempt_keeps_both; test_runtime.EvaluatorTests.test_duplicate_multiplicity` | SDK+PROXY | Failed attempt preserved; official penalty UNKNOWN |
| K53 | `test_runtime.DataTests.test_K53_missing_duplicate_rows; test_artifacts.ArtifactTests.test_atomic_no_clobber_and_failure_cleanup` | CORE | Exact integrity/atomic publication |
| K54 | `test_sdk_contract.SDKContracts.test_K13_K54_distinct_split_imports_and_full_coverage` | SDK | Public-only tools not pruned |

## Additional safety and workflow regressions

Contracts test nested duplicate/overflow/nonfinite JSON and strict Pydantic config,
labels and submissions. Artifacts test normalized/source/model/output overlaps,
atomic cleanup/refusal and recursive source identity; Windows junction escape is an
actual generated reparse fixture, with a separate symlink privilege skip reported.
Data tests source/fold/app-out exposure and label-free projection. Audio tests
chronological association/corruption/30-second boundary and lazy mocked resampling.
Loop tests deadline injection, one-session fatal/getter handling, trace retention,
internal DONE and bounded recovery. Preparation tests READ-to-WRITE/ASK/empty/DONE,
real observation-prefix drift and transient train-only state diagnostics. Training
tests token boundary/roundtrip/masks/pad==EOS, dry-run, actual lazy trainer options
through injected third-party modules, artifact identities and FAILED/INTERRUPTED
statuses. CLI tests complete public audio fixture orchestration and fatal trace
sidecars, with no real models/services. Packaging/guides validate offline paths,
examples and command surfaces. See implementation.md for actual counts/limitations.
