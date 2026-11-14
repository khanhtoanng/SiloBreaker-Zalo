"""Single next-action protocol; all eligible schemas and observed history retained."""

import json

SYSTEM = """Bạn xử lý yêu cầu tiếng Việt trong latest_user_text. Trả về đúng một JSON:
{"kind":"CALL","tool_name":"contacts.search","arguments":{"query":"Bảo"}}
{"kind":"ASK","tool_name":"sms.send","arguments":{"params":["content"]}}
{"kind":"DONE"}

Chọn bước tiếp theo theo thứ tự:
1. Xác định mục tiêu còn lại. Tôn trọng câu sửa lại, phủ định và hủy ở cuối yêu cầu.
   Dùng lịch sử để hiểu tham chiếu. Các thao tác trong lịch sử đã chạy.
2. Nếu có thể tiến hành một mục tiêu độc lập, hãy tiếp tục mục tiêu đó. Nếu cần dữ liệu,
   CALL công cụ đọc: tra danh bạ theo tên/quan hệ, lịch theo sự kiện, thiết bị theo phòng,
   hóa đơn theo dịch vụ, tài khoản và người thụ hưởng trước khi chuyển khoản. Khi chưa rõ
   bộ lọc, có thể gọi công cụ liệt kê với {} nếu schema cho phép. Dùng kết quả đọc và
   ngữ cảnh để điền tham số. Không đoán ID.
3. CALL công cụ thực hiện khi đã đủ dữ liệu. Dùng current_time, timezone và địa chỉ
   nhà/cơ quan trong hồ sơ. Giữ nguyên nội dung được yêu cầu. Bỏ tham số tùy chọn khi
   người dùng không nêu giá trị, kể cả label, repeat và bộ lọc. Kết quả done:false là
   chưa thành công. Không gọi lại thao tác đã thành công hoặc chưa rõ đã thực hiện chưa.
4. ASK kết thúc lượt ngay. Chỉ hỏi về tham số thật sự thiếu sau khi đã tận dụng ngữ
   cảnh, lịch sử và công cụ đọc, đồng thời đã xử lý các mục tiêu độc lập có thể thực
   hiện. Chẳng hạn “nhắn Bảo” chưa có nội dung; còn “nhắn Bảo là tôi đến trễ” thì cần
   tra Bảo và gửi nếu tìm thấy đúng người. Hỏi đúng tên tham số của công cụ đích.
5. DONE khi đã thực hiện xong, người dùng đã hủy, hoặc không có công cụ phù hợp.
Không gọi thêm để kiểm tra thao tác đã thành công. Không truy cập trạng thái ẩn.
"""


def compile_messages(
    sample, registry, observations, rejection=None, *, ledger=None, max_characters=None
):
    if not isinstance(sample.get("text"), str):
        raise ValueError(
            "This text baseline requires text; train CLI supplies authorized oracle transcripts"
        )
    payload = {
        "installed_tools": list(registry.values()),
        "context": sample.get("context", {}),
        "history": sample.get("history", []),
        "observations": observations,
        "normalization": sample.get("normalization"),
    }
    if ledger is not None:
        payload["goal_ledger"] = ledger
    if rejection:
        payload["previous_decision_rejected_before_execution"] = rejection
    payload["latest_user_text"] = sample["text"]
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    if (
        max_characters is not None
        and len(encoded.encode("utf-8")) + len(SYSTEM.encode("utf-8")) > max_characters
    ):
        raise ValueError("CONTEXT_OVERFLOW: required schemas/history/evidence cannot fit")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": encoded}]
