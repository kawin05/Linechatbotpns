from app.database import get_config


def handle_fallback(text: str) -> str:
    """Fallback when no command matches."""
    return "ไม่เข้าใจคำสั่งค่ะ พิมพ์ 'help' เพื่อดูคำสั่งที่มี"
