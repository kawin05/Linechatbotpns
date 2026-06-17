import re
from app.sheets import get_stock


def handle_stock(text: str) -> str:
    """Parse 'stock [product]' and return stock info."""
    match = re.match(r"stock\s+(.+)", text, re.IGNORECASE)
    if not match:
        return "ใช้คำสั่ง: stock [ชื่อสินค้า] เช่น stock แป้งผีเสื้อ"
    product = match.group(1).strip()
    return get_stock(product)
