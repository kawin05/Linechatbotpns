import re
from app.handlers.sales import handle_sales_today, handle_sales_month
from app.handlers.stock import handle_stock
from app.handlers.orders import handle_orders_today
from app.handlers.forward import handle_send
from app.handlers.help import handle_help
from app.handlers.llm_fallback import handle_fallback


def route_message(text: str, group_id: str | None = None) -> str:
    """Route a text message to the appropriate handler."""
    text = text.strip()

    if text == "ยอดวันนี้":
        return handle_sales_today()
    elif text == "ยอดเดือนนี้":
        return handle_sales_month()
    elif re.match(r"^stock\s+", text, re.IGNORECASE):
        return handle_stock(text)
    elif text == "ออเดอร์วันนี้":
        return handle_orders_today()
    elif text.startswith("/send"):
        return handle_send(text, group_id)
    elif text == "help":
        return handle_help()
    else:
        return handle_fallback(text)
