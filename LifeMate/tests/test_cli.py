import contextlib
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from test_audio import wav
from test_goals import goal
from test_loop import Policy
from test_runtime import CATALOG, FakeEnv

from lifemate.cli import build_parser, main
from lifemate.config import load_config
from lifemate.workflows import dispatch, package_check, predict


class UtilityConsumerTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def run_script(self, name, *args):
        with (
            patch.object(sys, "argv", [name, *map(str, args)]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            return runpy.run_path(str(self.root / "scripts" / name), run_name="__main__")

    def fixture(self, root, kit_name="wrapper/kit"):
        kit = root / kit_name
        split = kit / "train"
        split.mkdir(parents=True)
        (split / "train_tools_catalog.json").write_text(
            json.dumps(
                {
                    "apps": [
                        {
                            "id": app,
                            "tools": [tool for tool in CATALOG.values() if tool["app"] == app],
                        }
                        for app in ("contacts", "sms", "sys")
                    ]
                }
            )
        )
        rows = [
            {
                "id": sid,
                "audio_text": "Read contacts",
                "context": {"installed_apps": {"contacts": {"tools": ["contacts.search"]}}},
                "label": {"tool_calls": []},
            }
            for sid in ("a", "b")
        ]
        manifest = split / "train.jsonl"
        manifest.write_text("".join(json.dumps(row) + "\n" for row in rows))
        from lifemate.provenance import file_sha256

        fingerprint = file_sha256(manifest)
        fold = root / "fold.json"
        fold.write_text(
            json.dumps(
                {
                    "source_split": "train",
                    "seed": 1,
                    "dataset_sha256": fingerprint,
                    "fit_ids": ["a"],
                    "validation_ids": ["b"],
                }
            )
        )
        trajectories = root / "trajectories.jsonl"
        trajectories.write_text(
            "".join(
                json.dumps(
                    {
                        "scenario_id": sid,
                        "partition": partition,
                        "source_split": "train",
                        "fold": "grouped",
                        "step_index": 0,
                        "messages": [
                            {"role": "system", "content": "fixture"},
                            {"role": "user", "content": '{"observations":[]}'},
                            {"role": "assistant", "content": '{"kind":"DONE"}'},
                        ],
                    }
                )
                + "\n"
                for sid, partition in (("a", "fit"), ("b", "validation"))
            )
        )
        replay = root / "replay.json"
        replay.write_text(
            json.dumps(
                {
                    "dataset_sha256": fingerprint,
                    "records": [
                        {"id": sid, "state_hash": "a" * 64, "pass": True} for sid in ("a", "b")
                    ],
                }
            )
        )
        return kit, fold, trajectories, replay

    def arguments(self, name, selected, fold, trajectories, replay, out):
        args = ["--data-root", selected, "--out", out]
        if name == "check_trajectories.py":
            args += ["--split-config", fold, "--trajectories", trajectories]
        elif name == "check_evaluator.py":
            args += ["--replay", replay]
        return args

    def test_actual_ollama_smoke_preflights_tokenizer_source_existing_and_external_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tokenizer = root / "tokenizer"
            tokenizer.mkdir()
            existing = root / "existing.json"
            existing.write_text("keep")
            for out, error in (
                (tokenizer / "report.json", ValueError),
                (tokenizer / "nested/../report.json", ValueError),
                (self.root / "forbidden-r3-smoke.json", ValueError),
                (existing, FileExistsError),
            ):
                with (
                    self.subTest(out=out),
                    patch(
                        "lifemate.ollama_policy.OllamaPolicy",
                        side_effect=AssertionError("policy before output preflight"),
                    ) as factory,
                    self.assertRaises(error),
                ):
                    self.run_script("smoke_ollama.py", "--tokenizer-path", tokenizer, "--out", out)
                factory.assert_not_called()
            self.assertEqual(existing.read_text(), "keep")
            self.assertEqual(list(tokenizer.iterdir()), [])
            self.assertFalse((self.root / "forbidden-r3-smoke.json").exists())
            out = root / "external/report.json"
            policy = Mock(metadata={"backend": "authored-fake"}, last_usage={})
            policy.next_action.return_value = {"kind": "DONE"}
            with patch("lifemate.ollama_policy.OllamaPolicy", return_value=policy) as factory:
                self.run_script("smoke_ollama.py", "--tokenizer-path", tokenizer, "--out", out)
            factory.assert_called_once()
            self.assertEqual(factory.call_args.kwargs["tokenizer_path"], tokenizer)
            policy.next_action.assert_called_once()
            self.assertEqual(json.loads(out.read_text())["status"], "PASS")

    def test_workflows_protect_supplied_and_resolved_kit_before_processing_or_factories(self):
        from lifemate.config import InferenceConfig

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            kit, fold, trajectories, replay = self.fixture(root)
            sdk = kit / "train/zaic_tools"
            sdk.mkdir()
            (sdk / "__init__.py").write_text("# authored stub; no SDK session")
            predictions = root / "predictions.jsonl"
            predictions.write_text(
                json.dumps({"id": "b", "tool_calls": [], "state_hash": "a" * 64}) + "\n"
            )
            for selected in (kit, kit.parent, kit / "train/.."):
                forbidden = selected / "new-report.json"
                for command in (
                    "audit",
                    "freeze",
                    "replay",
                    "trajectories",
                    "evaluate",
                    "validate",
                    "predict",
                    "package-check",
                ):
                    values = {"data_root": selected, "out": forbidden}
                    if command in ("evaluate", "validate"):
                        values["predictions"] = predictions
                    if command == "evaluate":
                        values.update(replay=replay, split_config=fold)
                    if command in ("predict", "package-check"):
                        values.update(selection="all", input_mode="oracle", split="train")
                    with (
                        self.subTest(command=command, selected=selected),
                        patch(
                            "lifemate.workflows.load_manifest",
                            side_effect=AssertionError("manifest before output preflight"),
                        ),
                        patch(
                            "lifemate.workflows.load_catalog",
                            side_effect=AssertionError("catalog before output preflight"),
                        ),
                        patch(
                            "lifemate.workflows.create_policy",
                            side_effect=AssertionError("policy before preflight"),
                        ),
                        self.assertRaisesRegex(ValueError, "protected input"),
                    ):
                        dispatch(command, values)
                    self.assertFalse(forbidden.exists())
            # A sidecar can alias the supplied wrapper even when the main output
            # itself is external. All sidecars must pass before runtime factories.
            renamed_kit, _, _, _ = self.fixture(root / "sidecar", "result.diagnostics.json/kit")
            sdk = renamed_kit / "train/zaic_tools"
            sdk.mkdir()
            (sdk / "__init__.py").write_text("# authored")
            cfg = InferenceConfig(
                data_root=renamed_kit.parent,
                out=renamed_kit.parent.parent / "result.jsonl",
                selection="all",
            )
            with self.assertRaisesRegex(ValueError, "protected input"):
                predict(cfg, policy_factory=lambda _: self.fail("policy before sidecar preflight"))

    def test_external_wrapper_workflows_succeed_without_real_runtime(self):
        from lifemate.config import InferenceConfig

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            kit, fold, trajectories, replay = self.fixture(root)
            sdk = kit / "train/zaic_tools"
            sdk.mkdir()
            (sdk / "__init__.py").write_text("# authored; injected session only")
            result = dispatch("audit", {"data_root": kit.parent, "out": root / "audit.json"})
            self.assertEqual(result["kind"], "SAFE_CATALOG_AUDIT")
            cfg = InferenceConfig(
                data_root=kit.parent, out=root / "run/predict.jsonl", selection="all"
            )
            self.assertEqual(package_check(cfg)["status"], "STATIC_ONLY")
            result = predict(
                cfg,
                policy_factory=lambda _: Policy([{"kind": "DONE"}], goals=[]),
                env_factory=lambda *_: FakeEnv(),
            )
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(len(cfg.out.read_text().splitlines()), 2)

    def test_actual_smoke_policy_separate_planner_and_main_one_read(self):
        from test_runtime import SAMPLE

        from lifemate.runtime.loop import infer

        consumer = runpy.run_path(
            str(self.root / "scripts/smoke_runtime.py"), run_name="consumer_import"
        )
        policy = consumer["ReadOnce"]("contacts.search")
        planner = consumer["ReadPlan"]("contacts.search")
        request = {"latest_user_text": SAMPLE["text"]}
        self.assertEqual(planner.plan(request, deadline=1), policy.plan(request, deadline=1))
        self.assertFalse(policy.called)
        env = FakeEnv()
        prediction, diagnostic = infer(
            SAMPLE, ".", "train", CATALOG, policy, planner=planner, env_factory=lambda *_: env
        )
        self.assertEqual(diagnostic["stop_reason"], "DONE")
        self.assertEqual(prediction["tool_calls"], [{"name": "contacts.search", "arguments": {}}])
        self.assertEqual(env.events, ["validate", "call"])
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            kit, fold, trajectories, replay = self.fixture(root)
            out = root / "run/smoke.jsonl"

            def injected(*args, **kwargs):
                return infer(*args, **kwargs, env_factory=lambda *_: FakeEnv())

            with patch("lifemate.agent_loop.infer", side_effect=injected):
                self.run_script(
                    "smoke_runtime.py",
                    *self.arguments(
                        "smoke_runtime.py", kit.parent, fold, trajectories, replay, out
                    ),
                )
            self.assertEqual(len(json.loads(out.read_text())["tool_calls"]), 1)
            self.assertEqual(
                json.loads(out.with_suffix(".diagnostics.json").read_text())["stop_reason"], "DONE"
            )

    def test_all_utilities_preflight_direct_wrapper_alias_and_all_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            kit, fold, trajectories, replay = self.fixture(root)
            inputs = [fold, trajectories, replay]
            original = {p: p.read_bytes() for p in inputs}
            for name in ("check_trajectories.py", "check_evaluator.py", "smoke_runtime.py"):
                for selected in (kit, kit.parent, kit / "train/.."):
                    for out in (kit / "new.json", kit / "train/../alias.json"):
                        with (
                            self.subTest(name=name, selected=selected, out=out),
                            patch(
                                "lifemate.data_loader.load_manifest",
                                side_effect=AssertionError("work before output preflight"),
                            ),
                            self.assertRaisesRegex(ValueError, "protected input"),
                        ):
                            self.run_script(
                                name,
                                *self.arguments(name, selected, fold, trajectories, replay, out),
                            )
                        self.assertFalse(out.exists())
                protected = (
                    [fold, trajectories]
                    if name == "check_trajectories.py"
                    else [replay]
                    if name == "check_evaluator.py"
                    else []
                )
                for path in protected:
                    with (
                        self.subTest(name=name, input=path),
                        self.assertRaisesRegex(ValueError, "protected input"),
                    ):
                        self.run_script(
                            name, *self.arguments(name, kit, fold, trajectories, replay, path)
                        )
            self.assertEqual({p: p.read_bytes() for p in inputs}, original)

    def test_smoke_sidecar_exists_and_collision_fail_before_work(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            kit, fold, trajectories, replay = self.fixture(root)
            out = root / "smoke.jsonl"
            sidecar = out.with_suffix(".diagnostics.json")
            sidecar.write_text("keep")
            with (
                patch(
                    "lifemate.data_loader.load_catalog",
                    side_effect=AssertionError("runtime before preflight"),
                ),
                self.assertRaises(FileExistsError),
            ):
                self.run_script(
                    "smoke_runtime.py",
                    *self.arguments("smoke_runtime.py", kit, fold, trajectories, replay, out),
                )
            self.assertFalse(out.exists())
            self.assertEqual(sidecar.read_text(), "keep")
            kit, fold, trajectories, replay = self.fixture(
                root / "other", "wrapper/collision.diagnostics.json"
            )
            collision = kit.parent / "collision.jsonl"
            with (
                patch(
                    "lifemate.agent_loop.infer", side_effect=AssertionError("SDK before preflight")
                ),
                self.assertRaisesRegex(ValueError, "protected input"),
            ):
                self.run_script(
                    "smoke_runtime.py",
                    *self.arguments("smoke_runtime.py", kit, fold, trajectories, replay, collision),
                )
            self.assertFalse(collision.exists())

    def test_trajectory_and_evaluator_external_success_and_existing_no_clobber(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            kit, fold, trajectories, replay = self.fixture(root)
            for name in ("check_trajectories.py", "check_evaluator.py"):
                out = root / (name + ".json")
                args = self.arguments(name, kit.parent, fold, trajectories, replay, out)
                self.run_script(name, *args)
                self.assertEqual(json.loads(out.read_text())["status"], "PASS")
                before = out.read_bytes()
                with self.assertRaises(FileExistsError):
                    self.run_script(name, *args)
                self.assertEqual(out.read_bytes(), before)

    @unittest.skipUnless(os.name == "nt", "Windows junction contract")
    def test_utility_kit_and_sidecar_junction_aliases_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            kit, fold, trajectories, replay = self.fixture(root)
            alias = root / "alias.diagnostics.json"
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(kit)], capture_output=True
            )
            if result.returncode:
                self.skipTest("Junction creation unavailable: " + str(result.returncode))
            try:
                self.assertEqual(alias.resolve(), kit.resolve())
                for name in ("check_trajectories.py", "check_evaluator.py", "smoke_runtime.py"):
                    for selected in (kit.parent, alias):
                        with (
                            self.subTest(name=name, selected=selected),
                            patch(
                                "lifemate.data_loader.load_manifest",
                                side_effect=AssertionError("work before preflight"),
                            ),
                            self.assertRaisesRegex(ValueError, "protected input"),
                        ):
                            self.run_script(
                                name,
                                *self.arguments(
                                    name,
                                    selected,
                                    fold,
                                    trajectories,
                                    replay,
                                    alias / "forbidden.json",
                                ),
                            )
                with (
                    patch(
                        "lifemate.agent_loop.infer",
                        side_effect=AssertionError("SDK before sidecar preflight"),
                    ),
                    self.assertRaisesRegex(ValueError, "protected input"),
                ):
                    self.run_script(
                        "smoke_runtime.py",
                        *self.arguments(
                            "smoke_runtime.py",
                            kit,
                            fold,
                            trajectories,
                            replay,
                            root / "alias.jsonl",
                        ),
                    )
                self.assertFalse((kit / "forbidden.json").exists())
            finally:
                self.assertTrue(alias.absolute().is_relative_to(root))
                os.rmdir(alias)  # Remove the authored junction itself, never the kit target.
            self.assertTrue(kit.is_dir())


class CliTests(unittest.TestCase):
    def test_old_new_command_help_and_forwarding(self):
        parser = build_parser()
        for command in (
            "freeze",
            "predict",
            "evaluate",
            "trajectories",
            "validate",
            "train",
            "replay",
            "audit",
            "config-check",
            "compare",
            "asr-evaluate",
            "package-check",
        ):
            with (
                self.subTest(command=command),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit) as e,
            ):
                parser.parse_args([command, "--help"])
            self.assertEqual(e.exception.code, 0)
        seen = []
        with contextlib.redirect_stdout(io.StringIO()):
            main(
                ["predict", "--config", "outside.json", "--max-decisions", "6"],
                dispatcher=lambda command, args: seen.append((command, args)),
            )
        self.assertEqual(seen[0][1]["max_decisions"], 6)
        self.assertNotIn("sample_seconds", seen[0][1])

    def test_config_relative_paths_and_explicit_override_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config.json"
            p.write_text(
                json.dumps(
                    {"data_root": "kit", "out": "out", "selection": "all", "max_decisions": 4}
                )
            )
            c = load_config(p, "inference", {"max_decisions": 7})
            self.assertEqual(c.data_root, Path(d) / "kit")
            self.assertEqual(c.max_decisions, 7)

    def kit(self, root):
        split = root / "kit/public_test"
        split.mkdir(parents=True)
        (split / "zaic_tools").mkdir()
        (split / "zaic_tools/__init__.py").write_text("# synthetic; injected SDK")
        apps = []
        for app in ("contacts", "sms", "sys"):
            apps.append({"id": app, "tools": [t for t in CATALOG.values() if t["app"] == app]})
        (split / "public_test_tools_catalog.json").write_text(json.dumps({"apps": apps}))
        row = {
            "id": "x",
            "audio": "audio/latest.wav",
            "history": [{"role": "user", "audio": "audio/old.wav"}],
            "context": {
                "installed_apps": {
                    "sms": {"tools": ["sms.send"]},
                    "contacts": {"tools": ["contacts.search"]},
                },
                "profile": {"contact_id": "c1"},
            },
        }
        (split / "public_test.jsonl").write_text(json.dumps(row) + "\n")
        wav(split / "audio/latest.wav")
        wav(split / "audio/old.wav")
        asr = root / "asr"
        asr.mkdir()
        from lifemate.config import InferenceConfig

        return InferenceConfig(
            data_root=root / "kit",
            out=root / "run/result.jsonl",
            split="public_test",
            selection="all",
            input_mode="audio",
            asr_path=asr,
        )

    def test_complete_audio_pipeline_real_fields_and_atomic_final(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = self.kit(root)
            paths = []
            opened = []

            class ASR:
                def transcribe(self, path, *, deadline):
                    paths.append(path.name)
                    return "send c1 hello"

            env = FakeEnv()

            def factory(*args):
                opened.append(args)
                return env

            result = predict(
                cfg,
                policy_factory=lambda _: Policy(
                    [
                        {
                            "kind": "CALL",
                            "tool_name": "sms.send",
                            "arguments": {"contact_id": "c1", "content": "hello"},
                        },
                        {"kind": "DONE"},
                    ],
                    [goal()],
                ),
                asr_factory=lambda _: ASR(),
                env_factory=factory,
            )
            self.assertEqual(result["status"], "COMPLETE")
            run = json.loads(cfg.out.with_suffix(".run.json").read_text())
            self.assertEqual(run["input_mode"], "audio")
            self.assertEqual(run["split"], "public_test")
            self.assertEqual(run["settings"]["seed"], 20261109)
            self.assertEqual(run["backend"], "ollama")
            self.assertEqual(paths, ["old.wav", "latest.wav"])
            self.assertEqual(len(opened), 1)
            row = json.loads(cfg.out.read_text())
            self.assertEqual(row["tool_calls"], env.calls)
            self.assertEqual(set(row), {"id", "tool_calls", "state_hash"})
            self.assertEqual(
                json.loads(cfg.out.with_suffix(".run.json").read_text())["completed_ids"], ["x"]
            )

    def test_fatal_after_write_preserves_diagnostic_no_final(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = self.kit(Path(d))
            env = FakeEnv()

            class ASR:
                def transcribe(self, *a, **kw):
                    return "send c1 hello"

            class Broken(Policy):
                def next_action(self, *a, **kw):
                    if not env.calls:
                        return {
                            "kind": "CALL",
                            "tool_name": "sms.send",
                            "arguments": {"contact_id": "c1", "content": "hello"},
                        }
                    raise RuntimeError("secret transport token")

            with self.assertRaises(RuntimeError):
                predict(
                    cfg,
                    policy_factory=lambda _: Broken([], [goal()]),
                    asr_factory=lambda _: ASR(),
                    env_factory=lambda *_: env,
                )
            self.assertFalse(cfg.out.exists())
            diagnostic = json.loads(cfg.out.with_suffix(".diagnostics.json").read_text())
            self.assertEqual(diagnostic["records"][-1]["tool_calls"], env.calls)
            self.assertNotIn("secret", json.dumps(diagnostic))
            self.assertEqual(
                json.loads(cfg.out.with_suffix(".run.json").read_text())["status"], "FAILED"
            )

    def test_timed_submission_keeps_sdk_trace_and_exposes_timing(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = self.kit(Path(d))
            cfg = cfg.model_copy(update={"include_timing": True})
            env = FakeEnv()
            result = predict(
                cfg,
                policy_factory=lambda _: Policy([{"kind": "DONE"}], []),
                asr_factory=lambda _: Mock(transcribe=Mock(return_value="nothing")),
                env_factory=lambda *_: env,
            )
            row = json.loads(cfg.out.read_text())
            self.assertEqual(row["tool_calls"], env.get_tool_calls())
            self.assertEqual(row["state_hash"], env.get_state_hash())
            self.assertIs(type(row.get("time")), int)
            self.assertGreaterEqual(row["time"], 0)
            self.assertGreaterEqual(result["model_load_seconds"], 0)
            self.assertGreaterEqual(result["prediction_seconds"], 0)

    def test_replay_mismatch_preserves_nonzero_legacy_status(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            main(["replay"], dispatcher=lambda *a: {"counts": {"failed": 1}})
        self.assertEqual(raised.exception.code, 1)

    def test_success_returns_none_for_console_launcher(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["package-check"], dispatcher=lambda *_: {"status": "STATIC_ONLY"})
        self.assertIsNone(status)
        self.assertEqual(json.loads(output.getvalue()), {"status": "STATIC_ONLY"})

    def test_rejected_secret_config_value_is_not_echoed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "data_root": "kit",
                        "out": "out",
                        "selection": "all",
                        "api_key": "FAKE_TRANSPORT_SENTINEL",
                    }
                )
            )
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit):
                main(["config-check", "--kind", "inference", "--config", str(path)])
            self.assertNotIn("FAKE_TRANSPORT_SENTINEL", errors.getvalue())
            self.assertIn("api_key", errors.getvalue())

    def test_failure_after_one_completed_sample_keeps_checkpoint_not_final(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = self.kit(Path(d))
            manifest = cfg.data_root / "public_test/public_test.jsonl"
            row = json.loads(manifest.read_text())
            manifest.write_text(json.dumps(row) + "\n" + json.dumps({**row, "id": "y"}) + "\n")
            opened = []

            def factory(root, split, sid):
                opened.append(sid)
                if sid == "y":
                    raise RuntimeError("SDK initialization failed")
                return FakeEnv()

            class ASR:
                def transcribe(self, *a, **kw):
                    return "nothing"

            with self.assertRaises(RuntimeError):
                predict(
                    cfg,
                    policy_factory=lambda _: Policy([], []),
                    asr_factory=lambda _: ASR(),
                    env_factory=factory,
                )
            self.assertEqual(opened, ["x", "y"])
            self.assertFalse(cfg.out.exists())
            metadata = json.loads(cfg.out.with_suffix(".run.json").read_text())
            self.assertEqual(metadata["status"], "FAILED")
            self.assertEqual(metadata["selected_ids"], ["x", "y"])
            self.assertEqual(metadata["completed_ids"], ["x"])
            partial = [
                json.loads(line)
                for line in cfg.out.with_suffix(".partial.jsonl").read_text().splitlines()
            ]
            self.assertEqual([row["id"] for row in partial], ["x"])

    def test_prediction_does_not_replace_a_checkpoint_created_after_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = self.kit(Path(d))
            checkpoint = cfg.out.with_suffix(".partial.jsonl")

            def start_policy(_):
                checkpoint.write_text("created by another writer", encoding="utf-8")
                return Policy([], [])

            with self.assertRaises(FileExistsError):
                predict(
                    cfg,
                    policy_factory=start_policy,
                    asr_factory=lambda _: Mock(transcribe=Mock(return_value="nothing")),
                    env_factory=lambda *_: FakeEnv(),
                )

            self.assertEqual(checkpoint.read_text(encoding="utf-8"), "created by another writer")
            self.assertFalse(cfg.out.exists())
            metadata = json.loads(cfg.out.with_suffix(".run.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"], "FAILED")
            self.assertEqual(metadata["completed_ids"], [])
