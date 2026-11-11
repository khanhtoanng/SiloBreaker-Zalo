"""Independent adjacent-case review evidence; authored input and fake SDK only."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

from lifemate.metrics.asr import critical, evaluate_asr
from lifemate.runtime.loop import infer
from lifemate.runtime.normalize import normalize

root = Path.cwd()
work = root / "docs/ai/work/LM-002-python-structure-training-guide"
spec = importlib.util.spec_from_file_location("sealed_r1_normalize", work / "snapshots/after-20261110-r1/application/files/src/lifemate/runtime/normalize.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
context = {"current_time": "2026-11-10T10:00:00+07:00", "timezone": "Asia/Ho_Chi_Minh"}
cases = [
    ("tomorrow_half", "mai năm giờ à không, năm rưỡi", context, "2026-11-11T05:30:00+07:00"),
    ("tomorrow_hour", "nhắc mai 8 giờ à không, 9 giờ", context, "2026-11-11T09:00:00+07:00"),
    ("next_week", "thứ hai tuần sau 5 giờ à không, 6 giờ", context, "2026-11-16T06:00:00+07:00"),
    ("next_weekday", "thứ hai tới 5 giờ à không, 6 giờ", context, "2026-11-16T06:00:00+07:00"),
    ("multi_goal", "chuyển mười ba triệu và đặt xe mai năm giờ à không, năm rưỡi", context, "2026-11-11T05:30:00+07:00"),
    ("year_rollover", "mai 8 giờ à không, 9 giờ", {"current_time":"2026-12-31T23:50:00+07:00","timezone":"Asia/Ho_Chi_Minh"}, "2027-01-01T09:00:00+07:00"),
    ("relative_offset_basis", "nhắc sau 2 giờ à không, 3 giờ", context, "2026-11-10T13:00:00+07:00"),
    ("explicit_date_basis", "2026-12-31T23:00:00+07:00 à không, 22 giờ", context, "2026-12-31T22:00:00+07:00"),
    ("chained_corrections", "nhắc mai 8 giờ à không, 9 giờ à không 10 giờ", context, "2026-11-11T10:00:00+07:00"),
]
report = {"kind": "DETERMINISTIC_DEFECT_REPRODUCTION_NOT_PRODUCT_PASS", "cases": {}}
for name, text, clock, expected in cases:
    result = normalize(text, clock)
    slots = critical(text, clock)
    assert slots["time"] != [expected], name
    assert not result["uncertainties"], name
    assert all(not v["uncertain"] for v in result["values"]), name
    report["cases"][name] = {"text":text,"context":clock,"expected_or_uncertain":expected,"r2":result,"critical":slots,"sealed_r1":old.normalize(text,clock)}

# Verify that contradictory evidence reaches the actual runtime consumer. No real
# ToolEnv is opened; the policy chooses an empty plan and DONE for this probe.
sys.path.insert(0, str(root / "tests"))
from test_runtime import CATALOG, SAMPLE, FakeEnv

class Capture:
    def plan(self, request_context, *, deadline):
        self.request = request_context
        return {"goals":[]}
    def next_action(self, messages, *, deadline):
        self.messages = messages
        return {"kind":"DONE"}

sample = copy.deepcopy(SAMPLE)
sample["text"] = cases[0][1]
sample["context"].update(context)
policy = Capture()
env = FakeEnv()
prediction, diagnostic = infer(sample,".","train",CATALOG,policy,env_factory=lambda *_:env)
assert prediction["tool_calls"] == []
assert diagnostic["stop_reason"] == "DONE"
assert policy.request["normalization"]["effective_text"] == "mai năm rưỡi"
assert policy.request["normalization"]["values"][-1]["value"] == "2026-11-10T05:30:00+07:00"
report["actual_infer_planner_request"] = {"latest_user_text":policy.request["latest_user_text"],"normalization":policy.request["normalization"],"tool_calls":prediction["tool_calls"],"stop_reason":diagnostic["stop_reason"]}

reference = {"identity":{"policy":"same","fold":"authored"},"records":[{"id":"x","text":cases[0][1],"context":context}]}
candidate = {"identity":reference["identity"],"records":[{"id":"x","text":"mai năm rưỡi","context":context}]}
report["equivalent_corrected_and_final_transcripts"] = evaluate_asr(reference,candidate)
assert "time" in report["equivalent_corrected_and_final_transcripts"]["records"][0]["critical_slot_differences"]
evening = "mai 8 giờ tối à không, 9 giờ"
report["evening_qualifier_unresolved"] = {"r2":normalize(evening,context),"critical":critical(evening,context)}
assert report["evening_qualifier_unresolved"]["critical"]["time"] == ["2026-11-11T20:00:00+07:00","2026-11-10T09:00:00+07:00"]
assert report["evening_qualifier_unresolved"]["critical"]["uncertainty"]
print(json.dumps(report,ensure_ascii=True,indent=2))
