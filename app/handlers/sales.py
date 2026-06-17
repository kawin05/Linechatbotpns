from app.sheets import get_today_sales, get_monthly_sales


def handle_sales_today() -> str:
    return get_today_sales()


def handle_sales_month() -> str:
    return get_monthly_sales()
