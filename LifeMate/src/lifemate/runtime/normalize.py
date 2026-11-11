"""Conservative span evidence for Vietnamese quantities and sample-clock expressions."""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

NUMBERS = {
    "một": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "năm": 5,
    "sáu": 6,
    "bảy": 7,
    "tám": 8,
    "chín": 9,
    "mười": 10,
    "mười một": 11,
    "mười hai": 12,
}


def number(text):
    if re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        value = float(text.replace(",", "."))
        return value if math.isfinite(value) else None
    if text in NUMBERS:
        return NUMBERS[text]
    words = text.split()
    if len(words) == 2 and words[0] == "mười":
        unit = {"lăm": 5}.get(words[1], NUMBERS.get(words[1], 0))
        return 10 + unit if 1 <= unit <= 9 else None
    if len(words) in (2, 3) and words[1] == "mươi":
        tens = NUMBERS.get(words[0], 0)
        unit = {"mốt": 1, "lăm": 5}.get(words[-1], NUMBERS.get(words[-1], 0))
        if 2 <= tens <= 9 and (len(words) == 2 or 1 <= unit <= 9):
            return tens * 10 + (unit if len(words) == 3 else 0)
    return None


def sample_clock(context):
    value = context.get("current_time")
    if not value:
        raise ValueError("Sample current_time required for relative time")
    clock = datetime.fromisoformat(value.replace("Z", "+00:00"))
    zone = context.get("timezone")
    if zone:
        tz = ZoneInfo(zone)
        if clock.tzinfo is None:
            clock = clock.replace(tzinfo=tz)
        elif clock.utcoffset() != clock.astimezone(tz).utcoffset():
            raise ValueError("Sample current_time/timezone inconsistent")
        clock = clock.astimezone(tz)
    if clock.tzinfo is None:
        raise ValueError("Aware sample clock or timezone required")
    return clock


def normalize(text, context):
    result = {
        "raw_text": text,
        "effective_text": text,
        "values": [],
        "uncertainties": [],
        "negation_spans": [],
        "correction_spans": [],
    }
    lower = text.lower()
    corrections = list(re.finditer(r"\b(?:à không|ý tôi là)\b[, ]*", lower))
    # The word 'không' inside a correction marker is not part of its replacement
    # quantity, including when the speaker supplies no comma.
    quantity_text = "".join(
        "|" if any(m.start() <= i < m.end() for m in corrections) else char
        for i, char in enumerate(lower)
    )
    result["correction_spans"] = [[m.start(), m.end()] for m in corrections]
    result["negation_spans"] = [
        [m.start(), m.end()]
        for m in re.finditer(r"\b(?:đừng|hủy|không (?:đặt|gửi|chuyển|bật))\b", lower)
    ]
    time_info = {}

    def add(kind, value, m, uncertain=False):
        entry = {
            "kind": kind,
            "value": value,
            "span": [m.start(), m.end()],
            "text": text[m.start() : m.end()],
            "superseded": False,
            "uncertain": uncertain,
        }
        result["values"].append(entry)
        return entry

    def add_time(value, m, info, uncertain=False):
        entry = add("time", value.isoformat() if value is not None else None, m, uncertain)
        time_info[id(entry)] = {"start": m.start(), "end": m.end(), **info}
        return entry

    # Consume the complete numeric phrase, including unsupported compounds/signs.
    # Never salvage a certain suffix from e.g. 'trăm ba' or '1.000.000'.
    word = r"(?:mười|mươi|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|không|trăm|linh|lẻ|mốt|lăm|chục|vạn)"
    atom = r"(?:\d[\d.,]*|" + word + r")"
    token = r"(?:(?:[+\-−]\s*)?" + atom + r"(?:\s+" + atom + r")*)"
    boundary = r"(?<![\w.,+\-−])"
    amounts = list(
        re.finditer(
            boundary + r"(" + token + r")\s*(nghìn|ngàn|triệu|tỷ)\b(?:\s*(rưỡi)\b)?", quantity_text
        )
    )
    for index, m in enumerate(amounts):
        base = number(m.group(1))
        compound = any(
            not lower[a:b].strip()
            for a, b in (
                (amounts[index - 1].end(), m.start()) if index else (-1, -1),
                (m.end(), amounts[index + 1].start()) if index + 1 < len(amounts) else (-1, -1),
            )
            if a >= 0
        )
        if base is None or compound:
            result["uncertainties"].append(
                {"span": [m.start(), m.end()], "reason": "unsupported or ambiguous complete amount"}
            )
            continue
        unit = {"nghìn": 1000, "ngàn": 1000, "triệu": 1000000, "tỷ": 1000000000}[m.group(2)]
        value = (base + (0.5 if m.group(3) else 0)) * unit
        if not math.isfinite(value):
            result["uncertainties"].append(
                {"span": [m.start(), m.end()], "reason": "amount outside finite supported range"}
            )
            continue
        add("amount", int(value) if value % 1 == 0 else value, m)
    for m in re.finditer(
        boundary
        + r"("
        + token
        + r")\s*(?:giờ\b\s*|(?=rưỡi\b))(?:\s*(rưỡi\b|kém\s*(?:mười lăm\b|\d+\b)|\d+\b))?|(?<![\w:+\-−])([0-2]?\d):([0-5]\d)(?![\w:])",
        quantity_text,
    ):
        prefix = lower[: m.start()]
        if re.search(r"(?:sau|trước)\s*$", prefix) and not re.search(r"tuần\s+sau\s*$", prefix):
            continue
        if any(
            match.start() <= m.start() < match.end()
            for match in re.finditer(r"\d{4}-\d{2}-\d{2}T[0-9:+.Z-]+", text)
        ):
            continue
        hour = number(m.group(1)) if m.group(1) else int(m.group(3))
        if hour is None or hour % 1:
            result["uncertainties"].append(
                {"span": [m.start(), m.end()], "reason": "unsupported complete clock quantity"}
            )
            continue
        part = m.group(2) or ""
        minute = int(m.group(4)) if m.group(4) else 30 if part == "rưỡi" else 0
        if part.startswith("kém"):
            match = re.search(r"\d+", part)
            n = 15 if "mười lăm" in part else int(match.group()) if match else 0
            hour -= 1
            minute = 60 - n
        elif part.isdigit():
            minute = int(part)
        raw_hour = int(hour)
        period_match = re.match(r"\s*(sáng|chiều|tối)\b", lower[m.end() :])
        period_prefix = re.search(r"\b(sáng|chiều|tối)\s*$", lower[: m.start()])
        period = (
            period_match.group(1)
            if period_match
            else period_prefix.group(1)
            if period_prefix
            else ""
        )
        if period_match and period_prefix and period_match.group(1) != period_prefix.group(1):
            result["uncertainties"].append(
                {
                    "span": [period_prefix.start(), m.end() + period_match.end()],
                    "reason": "conflicting clock periods",
                }
            )
            continue
        if period in ("tối", "chiều") and 1 <= hour < 12:
            hour += 12
        if period == "sáng" and hour == 12:
            hour = 0
        if not 0 <= hour < 24 or not 0 <= minute < 60:
            result["uncertainties"].append(
                {"span": [m.start(), m.end()], "reason": "invalid clock expression"}
            )
            continue
        try:
            clock = sample_clock(context)
            day = clock
            # Qualifiers belong to this intent clause, never the whole utterance.
            separators = (
                list(re.finditer(r"[,;!?\n]|\.(?!\d)|\b(?:và|rồi|nhưng|sau đó|đồng thời)\b", lower))
                + corrections
            )
            start = max((s.end() for s in separators if s.end() <= m.start()), default=0)
            end = min((s.start() for s in separators if s.start() >= m.end()), default=len(text))
            clause = lower[start:end]
            weekdays = {
                "thứ hai": 0,
                "thứ ba": 1,
                "thứ tư": 2,
                "thứ năm": 3,
                "thứ sáu": 4,
                "thứ bảy": 5,
                "chủ nhật": 6,
            }
            qualifiers = list(
                re.finditer(
                    r"\b(?:ngày mai|mai|hôm nay|(?:thứ hai|thứ ba|thứ tư|thứ năm|thứ sáu|thứ bảy|chủ nhật)(?: tới| tuần sau)?)\b",
                    clause,
                )
            )
            if len(qualifiers) > 1:
                raise ValueError("ambiguous local day qualifiers")
            qualifier = qualifiers[0].group() if qualifiers else ""
            expression_start, expression_end = m.start(), m.end()
            if period_prefix:
                expression_start = period_prefix.start()
            if period_match:
                expression_end = m.end() + period_match.end()
            if qualifiers:
                q = qualifiers[0]
                a, b = start + q.start(), start + q.end()
                gap = lower[b : m.start()] if b <= m.start() else lower[m.end() : a]
                if not (b <= m.start() or a >= m.end()) or not re.fullmatch(
                    r"\s*(?:(?:lúc|vào|sáng|trưa|chiều|tối)\s*)?", gap
                ):
                    raise ValueError("unresolved local day qualifier association")
                expression_start = min(a, expression_start)
                expression_end = max(b, expression_end)
            if qualifier in ("mai", "ngày mai"):
                day += timedelta(days=1)
            for word, index in weekdays.items():
                if qualifier == word:
                    raise ValueError("weekday requires an explicit relative qualifier")
                if qualifier in (word + " tới", word + " tuần sau"):
                    delta = (index - clock.weekday()) % 7 or 7
                    if qualifier.endswith("tuần sau"):
                        delta = 7 - clock.weekday() + index
                    day = clock + timedelta(days=delta)
            value = day.replace(hour=int(hour), minute=minute, second=0, microsecond=0)
            add_time(
                value,
                m,
                {
                    "mode": "clock",
                    "hour": raw_hour,
                    "minute": minute,
                    "period": period,
                    "explicit_day": bool(qualifier),
                    "start": expression_start,
                    "end": expression_end,
                },
            )
        except (ValueError, KeyError) as exc:
            result["uncertainties"].append({"span": [m.start(), m.end()], "reason": str(exc)})
    for m in re.finditer(r"\b(?:sau|trước)\s+(\d+)\s*(phút|giờ|ngày)\b", lower):
        if re.search(r"tuần\s*$", lower[: m.start()]):
            continue
        try:
            delta = timedelta(
                **{{"phút": "minutes", "giờ": "hours", "ngày": "days"}[m.group(2)]: int(m.group(1))}
            )
            add_time(
                sample_clock(context) + (delta if m.group().startswith("sau") else -delta),
                m,
                {
                    "mode": "relative",
                    "direction": 1 if m.group().startswith("sau") else -1,
                    "unit": {"phút": "minutes", "giờ": "hours", "ngày": "days"}[m.group(2)],
                },
            )
        except (ValueError, OverflowError) as exc:
            result["uncertainties"].append({"span": [m.start(), m.end()], "reason": str(exc)})
    for m in re.finditer(r"(?<![\w+\-])\d{4}-\d{2}-\d{2}(?:T[0-9:+.Z-]+)?(?![\w:+.\-])", text):
        try:
            value = datetime.fromisoformat(m.group())
            if value.tzinfo is None:
                value = value.replace(tzinfo=sample_clock(context).tzinfo)
            add_time(value, m, {"mode": "explicit"})
        except ValueError:
            result["uncertainties"].append(
                {"span": [m.start(), m.end()], "reason": "invalid explicit date"}
            )
    # Bare duration units are meaningful only as adjacent correction candidates;
    # they cannot acquire an absolute clock/default date independently.
    for m in re.finditer(boundary + r"(" + token + r")\s*(phút|ngày)\b", quantity_text):
        if not any(
            c.end() <= m.start() and not lower[c.end() : m.start()].strip() for c in corrections
        ):
            continue
        quantity = number(m.group(1))
        if quantity is not None and quantity >= 0:
            add_time(
                None,
                m,
                {
                    "mode": "duration",
                    "quantity": quantity,
                    "unit": {"phút": "minutes", "ngày": "days"}[m.group(2)],
                },
                uncertain=True,
            )

    # Corrections bind complete local expressions. A clock scalar can inherit
    # date/timezone/period, while a relative scalar inherits direction and uses
    # its stated unit. Explicit new bases override old ones. Unknown binding
    # taints every affected temporal entry, never just a marker-level message.
    removed = []
    boundaries = [
        m
        for m in re.finditer(r"[,;!?\n]|\.(?!\d)|\b(?:và|rồi|nhưng|sau đó|đồng thời)\b", lower)
        if not any(c.start() <= m.start() < c.end() for c in corrections)
        and not any(
            m.end() <= c.start() and re.fullmatch(r"[\s,]*", lower[m.end() : c.start()])
            for c in corrections
        )
    ]
    for correction in corrections:
        local_start = max((b.end() for b in boundaries if b.end() <= correction.start()), default=0)
        local_end = min(
            (b.start() for b in boundaries if b.start() >= correction.end()), default=len(text)
        )
        before = [
            v
            for v in result["values"]
            if local_start <= v["span"][0] and v["span"][1] <= correction.start()
        ]
        after = [v for v in result["values"] if correction.end() <= v["span"][0] < local_end]
        previous = max(before, key=lambda v: v["span"][1], default=None)
        replacement = min(after, key=lambda v: v["span"][0], default=None)
        old_info = time_info.get(id(previous), {})
        new_info = time_info.get(id(replacement), {})
        linked = (
            previous
            and replacement
            and previous["kind"] == replacement["kind"]
            and re.fullmatch(
                r"[\s,]*", lower[old_info.get("end", previous["span"][1]) : correction.start()]
            )
            and not lower[correction.end() : new_info.get("start", replacement["span"][0])].strip()
        )
        if linked and previous["kind"] == "time":
            try:
                if previous["uncertain"] or not old_info or not new_info:
                    raise ValueError("unresolved preceding temporal basis")
                if re.match(
                    r"\s*(?:sáng|chiều|tối|trưa|đêm|kém|rưỡi|phút|ngày)\b",
                    lower[new_info["end"] : local_end],
                ):
                    raise ValueError("unsupported trailing temporal qualifier")
                if new_info["mode"] in ("relative", "explicit"):
                    value = datetime.fromisoformat(replacement["value"])
                elif (
                    old_info["mode"] == "relative"
                    and new_info["mode"] in ("clock", "duration")
                    and not new_info.get("explicit_day")
                    and not new_info.get("period")
                ):
                    quantity = new_info.get(
                        "quantity", number(replacement["text"].split("giờ")[0].strip())
                    )
                    if quantity is None or new_info.get("minute", 0):
                        raise ValueError("ambiguous relative-duration correction")
                    unit = new_info.get("unit", "hours")
                    value = sample_clock(context) + timedelta(
                        **{unit: old_info["direction"] * quantity}
                    )
                    new_info.update(mode="relative", direction=old_info["direction"], unit=unit)
                elif new_info["mode"] == "clock":
                    if old_info["mode"] == "relative" and not new_info["explicit_day"]:
                        raise ValueError("relative-to-clock correction needs an explicit day")
                    old_value = datetime.fromisoformat(previous["value"])
                    parsed = datetime.fromisoformat(replacement["value"])
                    day = parsed if new_info["explicit_day"] else old_value
                    period = new_info["period"] or old_info.get("period", "")
                    hour = new_info["hour"]
                    if period in ("chiều", "tối") and 1 <= hour < 12:
                        hour += 12
                    if period == "sáng" and hour == 12:
                        hour = 0
                    value = day.replace(
                        hour=hour, minute=new_info["minute"], second=0, microsecond=0
                    )
                    new_info["period"] = period
                else:
                    raise ValueError("unsupported temporal correction association")
                replacement.update(value=value.isoformat(), uncertain=False)
                previous["superseded"] = True
                new_info["correction_start"] = old_info.get("correction_start", old_info["start"])
                continue
            except (ValueError, OverflowError, TypeError, KeyError):
                linked = False
        if (previous and previous["kind"] == "time") or (
            replacement and replacement["kind"] == "time"
        ):
            for value in result["values"]:
                if value["kind"] == "time" and local_start <= value["span"][0] < local_end:
                    value["uncertain"] = True
            result["uncertainties"].append(
                {
                    "span": [local_start, local_end],
                    "reason": "unresolved temporal correction basis; affected values uncertain",
                }
            )
            continue
        if linked:
            previous["superseded"] = True
            removed.extend([previous["span"], [correction.start(), correction.end()]])
        else:
            if previous and not lower[previous["span"][1] : correction.start()].strip():
                previous["uncertain"] = True
            result["uncertainties"].append(
                {
                    "span": [correction.start(), correction.end()],
                    "reason": "unresolved correction scope; raw intents retained",
                }
            )
    edits = [(a, b, "") for a, b in removed]
    for entry in result["values"]:
        info = time_info.get(id(entry), {})
        if "correction_start" in info and not entry["superseded"] and not entry["uncertain"]:
            trailing_space = re.search(r"\s+$", text[info["correction_start"] : info["end"]])
            rendered = entry["value"] + (trailing_space.group() if trailing_space else "")
            edits.append((info["correction_start"], info["end"], rendered))
    effective = text
    for a, b, replacement_text in sorted(edits, reverse=True):
        effective = effective[:a] + replacement_text + effective[b:]
    result["effective_text"] = effective
    if re.search(r"\b(?:lát nữa|vài|khoảng|nửa triệu)\b", lower):
        result["uncertainties"].append(
            {"span": [0, len(text)], "reason": "unsupported or ambiguous quantity"}
        )
    return result
