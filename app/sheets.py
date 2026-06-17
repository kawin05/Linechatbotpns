import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_sheets_service():
    creds_json = json.loads(settings.GOOGLE_SHEETS_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def read_sheet(sheet_id: str, range_name: str) -> list[list[str]]:
    """Read a range from a Google Sheet. Returns rows as list of lists."""
    service = _get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()
    return result.get("values", [])


def get_today_sales() -> str:
    """Read today's sales total from the sales sheet."""
    rows = read_sheet(settings.SALES_SHEET_ID, "A:C")
    if len(rows) < 2:
        return "ไม่มีข้อมูลยอดขายวันนี้"
    last_row = rows[-1]
    date, total, orders = last_row[0], last_row[1], last_row[2] if len(last_row) > 2 else "0"
    return f"ยอดขายวันนี้ {total} บาท ({orders} ออเดอร์)"


def get_monthly_sales() -> str:
    """Read monthly sales total."""
    rows = read_sheet(settings.SALES_SHEET_ID, "E:G")
    if len(rows) < 2:
        return "ไม่มีข้อมูลยอดขายเดือนนี้"
    last_row = rows[-1]
    return f"ยอดขายเดือนนี้ {last_row[1]} บาท"


def get_stock(product: str) -> str:
    """Check stock level for a product."""
    rows = read_sheet(settings.STOCK_SHEET_ID, "A:B")
    for row in rows[1:]:  # skip header
        if product.lower() in row[0].lower():
            return f"{row[0]} คงเหลือ {row[1]} ชิ้น"
    return f"ไม่พบสินค้า '{product}' ในสต็อก"


def get_today_orders() -> str:
    """Read today's orders."""
    rows = read_sheet(settings.ORDERS_SHEET_ID, "A:D")
    if len(rows) < 2:
        return "วันนี้ไม่มีออเดอร์"
    orders = rows[1:]  # skip header
    lines = [f"{o[0]} | {o[1]} | {o[2]}" for o in orders[-5:]]  # last 5
    return "ออเดอร์วันนี้:\n" + "\n".join(lines)
