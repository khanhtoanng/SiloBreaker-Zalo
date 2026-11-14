"""Request-scoped evidence ledger. Model hypotheses never establish tool effects."""

from __future__ import annotations

import json

from ..contracts import Goal, GoalOccurrence, GoalPlan, json_loads
from .validation import Rejected

PLANNER_SYSTEM = """Xác định các thao tác cuối cùng được yêu cầu trong latest_user_text.
Trả về một JSON ngắn gọn. Ví dụ 'Nhắn Lan đi' khi có sms.send:
{"goals":[{"id":"g1","intent":"Nhắn Lan","tool_name":"sms.send","arguments":{},"dependencies":[],"condition":null,"occurrences":[{"id":"o1","span":[0,8]}]}]}
Chỉ dùng tên công cụ đã cài. Liệt kê các mục tiêu độc lập mà người dùng muốn làm ngay.
Mục tiêu báo thức/nhắc việc để làm việc khác sau này không yêu cầu làm việc đó ngay.
Giữ mục tiêu kể cả khi cần tra cứu thêm. Chỉ thêm công cụ đọc vào goals khi người dùng
yêu cầu xem kết quả của nó. Tra cứu để lấy ID, thời gian hoặc số tiền là bước ngầm định.
Dùng ID ngắn và duy nhất. dependencies chỉ chứa ID mục tiêu khác có trong goals khi
thật sự phải chờ mục tiêu đó xong. Bỏ arguments nếu giá trị chưa có dạng chính xác
theo schema. Không đoán ID, thời gian, số tiền, hoặc giá trị mặc định.
span là chỉ số ký tự Python trong latest_user_text, tính từ 0, không gồm vị trí cuối.
Nếu cùng thao tác được yêu cầu nhiều lần, mỗi occurrence có một span riêng.
Dùng lịch sử để hiểu tham chiếu. Tôn trọng câu sửa lại và phủ định, kể cả 'à thôi khỏi'.
Nếu đã hủy hoặc công cụ không hỗ trợ, trả {"goals":[]}.
Với mục tiêu có điều kiện, condition là {tool_name,field,operator,value}, gồm công cụ
đọc, đường dẫn trường kết quả và toán tử eq/ne/gt/ge/lt/le/contains. Chỉ khai báo
điều kiện khi thực sự cần kiểm tra; không đoán kết quả hoặc tự đánh dấu hoàn thành."""


class PolicyPlanner:
    def __init__(self, policy):
        self.policy = policy

    def plan(self, request_context: dict, *, deadline: float) -> GoalPlan:
        raw = self.policy.next_action(
            [
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user", "content": json.dumps(request_context, ensure_ascii=False)},
            ],
            deadline=deadline,
        )
        return GoalPlan.model_validate(json_loads(raw) if isinstance(raw, str) else raw)


class Ledger:
    def __init__(self, plan, text, registry):
        self.goals = GoalPlan.model_validate(
            plan.model_dump() if isinstance(plan, GoalPlan) else plan
        ).goals
        self.registry = registry
        ids = [g.id for g in self.goals]
        if len(ids) != len(set(ids)):
            raise Rejected("Duplicate goal IDs")
        occurrences = set()
        spans: list[tuple[str, int, int]] = []
        for goal in self.goals:
            if goal.tool_name not in registry or goal.tool_name == "sys.ask_missing_info":
                raise Rejected("Goal tool unavailable")
            if any(d not in ids or d == goal.id for d in goal.dependencies):
                raise Rejected("Unknown/self goal dependency")
            if goal.condition and (
                goal.condition.tool_name not in registry
                or registry[goal.condition.tool_name]["kind"] != "read"
            ):
                raise Rejected("Condition requires an eligible read observation")
            for occurrence in goal.occurrences:
                a, b = occurrence.span
                if occurrence.id in occurrences or not 0 <= a < b <= len(text):
                    raise Rejected("Invalid occurrence/span")
                if (
                    occurrence.status != "PENDING"
                    or occurrence.observation_ids
                    or occurrence.attempts
                ):
                    raise Rejected("Planner cannot claim effects/status")
                if any(goal.tool_name == tool and max(a, x) < min(b, y) for tool, x, y in spans):
                    raise Rejected("Repeated occurrences require distinct explicit spans")
                occurrences.add(occurrence.id)
                spans.append((goal.tool_name, a, b))

        def walk(identifier, stack):
            if identifier in stack:
                raise Rejected("Cyclic goals")
            for dep in self.goal(identifier).dependencies:
                walk(dep, stack + [identifier])

        for identifier in ids:
            walk(identifier, [])
        self.noops = {}

    def goal(self, identifier: str) -> Goal:
        return next(g for g in self.goals if g.id == identifier)

    def complete(self, goal: Goal) -> bool:
        return all(o.status == "COMPLETE" for o in goal.occurrences)

    def condition(self, goal, observations):
        c = goal.condition
        if c is None:
            return True
        matching = [
            o
            for o in observations
            if o["name"] == c.tool_name and o["outcome"] == "READ_OBSERVATION"
        ]
        if not matching:
            return None
        value = matching[-1]["result"]
        for part in c.field.split("."):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        if type(value) is bool or type(c.value) is bool:
            if type(value) is not type(c.value):
                return None
        if c.operator in ("gt", "ge", "lt", "le") and (
            type(value) not in (int, float) or type(c.value) not in (int, float)
        ):
            return None
        try:
            return {
                "eq": lambda: value == c.value,
                "ne": lambda: value != c.value,
                "gt": lambda: value > c.value,
                "ge": lambda: value >= c.value,
                "lt": lambda: value < c.value,
                "le": lambda: value <= c.value,
                "contains": lambda: c.value in value,
            }[c.operator]()
        except (TypeError, ValueError):
            return None

    def candidates(
        self, name: str, args: dict, observations: list[dict]
    ) -> list[tuple[Goal, GoalOccurrence]]:
        candidates = []
        for g in self.goals:
            if g.tool_name != name or any(args.get(k) != v for k, v in g.arguments.items()):
                continue
            if any(not self.complete(self.goal(d)) for d in g.dependencies):
                continue
            condition = self.condition(g, observations)
            if condition is False:
                for o in g.occurrences:
                    if o.status == "PENDING":
                        o.status = "CANCELED"
                continue
            if condition is not True:
                continue
            for o in g.occurrences:
                if o.status == "PENDING":
                    candidates.append((g, o))
        return candidates

    def bind(
        self, name: str, args: dict, observations: list[dict], choice: str | None = None
    ) -> tuple[Goal, GoalOccurrence]:
        candidates = self.candidates(name, args, observations)
        if choice is not None:
            candidates = [pair for pair in candidates if pair[1].id == choice]
        if len(candidates) != 1:
            raise Rejected("Write binding unresolved or no pending compatible occurrence")
        g, o = candidates[0]
        if o.attempts:
            previous = self.noops.get(o.id)
            # A no-effect may recover only after a NEW read and changed arguments.
            if previous is None or not self.recovery_proven(name, previous, args, observations):
                raise Rejected("No-effect retry lacks new corrective observation/arguments")
            if o.attempts >= 2:
                raise Rejected("Recovery cap reached")
        return g, o

    def recovery_proven(self, name, previous, args, observations):
        old, index = previous
        message = observations[index]["result"].get("message")
        reads = [x for x in observations[index + 1 :] if x["outcome"] == "READ_OBSERVATION"]
        changed = {k for k in set(old) | set(args) if old.get(k) != args.get(k)}
        if (
            name != "banking.transfer"
            or not changed
            or not changed <= {"from_account_id", "beneficiary_id"}
        ):
            return False
        accounts = [
            item
            for x in reads
            if x["name"] == "banking.get_balance" and isinstance(x["result"], dict)
            for item in x["result"].get("accounts", [])
            if isinstance(item, dict)
        ]
        beneficiaries = [
            item
            for x in reads
            if x["name"] == "banking.list_beneficiaries" and isinstance(x["result"], dict)
            for item in x["result"].get("beneficiaries", [])
            if isinstance(item, dict)
        ]
        if message == "số dư không đủ":
            return changed == {"from_account_id"} and any(
                item.get("id") == args.get("from_account_id")
                and type(item.get("balance")) in (int, float)
                and type(args.get("amount")) is int
                and item["balance"] >= args["amount"]
                for item in accounts
            )
        if message == "không tìm thấy tài khoản hoặc người thụ hưởng":
            return all(
                any(
                    item.get("id") == args.get(key)
                    for item in (accounts if key == "from_account_id" else beneficiaries)
                )
                for key in changed
            )
        return False

    def record(self, g, o, outcome, args, index):
        o.attempts += 1
        o.observation_ids.append(index)
        if outcome == "WRITE_EFFECT" or (
            outcome == "READ_OBSERVATION" and self.registry[g.tool_name]["kind"] == "read"
        ):
            o.status = "COMPLETE"
        elif outcome == "BUSINESS_NOOP":
            self.noops[o.id] = (args, index)
        else:
            o.status = "QUARANTINED"

    def pending(self, observations):
        for g in self.goals:
            if self.condition(g, observations) is False:
                for o in g.occurrences:
                    if o.status == "PENDING":
                        o.status = "CANCELED"
        return [o.id for g in self.goals for o in g.occurrences if o.status == "PENDING"]

    def dump(self):
        return [g.model_dump() for g in self.goals]
