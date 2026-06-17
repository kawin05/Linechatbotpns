import re
from app.database import get_forward_target
from app.line_bot import push_message


def handle_send(text: str, group_id: str | None = None) -> str:
    """Parse '/send [target] [message]' and forward."""
    match = re.match(r"/send\s+(.+?)\s+(.+)", text, re.DOTALL)
    if not match:
        return "ใช้: /send [ชื่อ] [ข้อความ] หรือ /send group [ข้อความ]"

    target = match.group(1).strip().lower()
    message = match.group(2).strip()

    if target == "group":
        if not group_id:
            return "ไม่พบ group ID"
        if push_message(group_id, message):
            return "ส่งข้อความถึงกลุ่มแล้ว"
        return "ส่งข้อความไม่สำเร็จ กรุณาลองใหม่"

    user_id = get_forward_target(target)
    if not user_id:
        return f"ไม่พบ '{target}' ในรายชื่อผู้รับ"

    if push_message(user_id, message):
        return f"ส่งข้อความถึง {target} แล้ว"
    return f"ส่งข้อความถึง {target} ไม่สำเร็จ"
