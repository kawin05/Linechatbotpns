from app.sheets import get_today_orders


def handle_orders_today() -> str:
    return get_today_orders()
