# LINE OA Team Bot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LINE OA bot that lets Kawin05's team query sales/stock/orders from Google Sheets, forwards messages to individuals or the group, and sends auto-alerts via Hermes cron.

**Architecture:** FastAPI server receiving LINE webhooks, routing commands to Google Sheets API, with Supabase for team data and config. Rule-based command parsing with optional LLM fallback.

**Tech Stack:** FastAPI, Supabase (Python client), Google Sheets API, LINE Messaging API SDK, Python 3.11+

**Project root:** `C:\Users\Kawin05\Desktop\line-team-bot\`

---

### Task 1: Project scaffolding + config module

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `.env.example`

- [ ] **Step 1: Create project directory structure**

```bash
mkdir -p /c/Users/Kawin05/Desktop/line-team-bot/app/handlers
mkdir -p /c/Users/Kawin05/Desktop/line-team-bot/supabase
cd /c/Users/Kawin05/Desktop/line-team-bot
```

- [ ] **Step 2: Create `app/__init__.py`**

Empty file.

- [ ] **Step 3: Create `app/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LINE
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS: str = ""  # JSON string or path
    SALES_SHEET_ID: str = ""
    STOCK_SHEET_ID: str = ""
    ORDERS_SHEET_ID: str = ""

    # LLM Fallback (optional)
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: str = "openai"  # openai | anthropic

    # App
    PROJECT_NAME: str = "LINE Team Bot"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: Create `.env.example`**

```
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
SUPABASE_URL=
SUPABASE_ANON_KEY=
GOOGLE_SHEETS_CREDENTIALS=
SALES_SHEET_ID=
STOCK_SHEET_ID=
ORDERS_SHEET_ID=
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
```

- [ ] **Step 5: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
venv/
*.db
```

- [ ] **Step 6: Commit**

```bash
git init
git add app/__init__.py app/config.py .env.example .gitignore
git commit -m "chore: scaffold project and config module"
```

---

### Task 2: Supabase schema + database module

**Files:**
- Create: `supabase/schema.sql`
- Create: `app/database.py`

- [ ] **Step 1: Create Supabase schema**

Write `supabase/schema.sql`:

```sql
-- Team members (who can use the bot)
CREATE TABLE IF NOT EXISTS team_members (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  line_user_id TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Forward targets (who can receive DMs)
CREATE TABLE IF NOT EXISTS forward_targets (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  line_user_id TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Message logs
CREATE TABLE IF NOT EXISTS message_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  command TEXT,
  reply TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bot config (key-value for system prompt, thresholds, sheet IDs)
CREATE TABLE IF NOT EXISTS bot_config (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value TEXT NOT NULL
);

-- Seed default system prompt
INSERT INTO bot_config (key, value) VALUES ('system_prompt', 'คุณคือบอทช่วยงานทีมขายของ Kawin05
- ตอบเป็นภาษาไทย สั้น กระชับ ไม่เกิน 3 ประโยค
- ใช้ภาษาเป็นกันเอง แต่สุภาพ
- ถ้าไม่เข้าใจคำสั่ง ให้บอกว่าไม่เข้าใจและแนะนำให้พิมพ์ help') ON CONFLICT (key) DO NOTHING;
```

- [ ] **Step 2: Create `app/database.py`**

```python
from supabase import create_client, Client
from app.config import settings

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY
)

def get_config(key: str) -> str | None:
    """Read a bot_config value by key."""
    result = supabase.table("bot_config").select("value").eq("key", key).execute()
    if result.data:
        return result.data[0]["value"]
    return None

def log_message(user_id: str, command: str | None, reply: str | None):
    """Log a message exchange."""
    supabase.table("message_logs").insert({
        "user_id": user_id,
        "command": command,
        "reply": reply
    }).execute()

def get_forward_target(name: str) -> str | None:
    """Get LINE user ID for a forward target by name."""
    result = supabase.table("forward_targets").select("line_user_id").eq("name", name).execute()
    if result.data:
        return result.data[0]["line_user_id"]
    return None
```

- [ ] **Step 3: Commit**

```bash
git add supabase/schema.sql app/database.py
git commit -m "feat: add Supabase schema and database module"
```

---

### Task 3: Google Sheets reader

**Files:**
- Create: `app/sheets.py`

- [ ] **Step 1: Create `app/sheets.py`**

```python
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
    # Expects rows: [date, total, orders_count]
    # Returns the latest row where date matches today
    # Simplified: returns last row as most recent
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
```

- [ ] **Step 2: Commit**

```bash
git add app/sheets.py
git commit -m "feat: add Google Sheets reader with sales/stock/order queries"
```

---

### Task 4: LINE Messaging API wrapper

**Files:**
- Create: `app/line_bot.py`

- [ ] **Step 1: Create `app/line_bot.py`**

```python
import hashlib
import hmac
import base64
from fastapi import HTTPException
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage, PushMessageRequest
)
from app.config import settings

configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)


def verify_signature(body: bytes, signature: str | None) -> bool:
    """Verify LINE webhook signature."""
    if not signature:
        return False
    hash_digest = hmac.new(
        settings.LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    computed = base64.b64encode(hash_digest).decode("utf-8")
    return hmac.compare_digest(computed, signature)


def reply_message(reply_token: str, text: str):
    """Reply to a LINE message."""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )


def push_message(user_id: str, text: str):
    """Send a push message to a specific LINE user."""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=text)]
            )
        )


def push_group_message(group_id: str, text: str):
    """Send a message to a LINE group."""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text=text)]
            )
        )
```

- [ ] **Step 2: Commit**

```bash
git add app/line_bot.py
git commit -m "feat: add LINE Messaging API wrapper (reply, push, verify)"
```

---

### Task 5: Command router + all handlers

**Files:**
- Create: `app/handlers/__init__.py`
- Create: `app/handlers/router.py`
- Create: `app/handlers/sales.py`
- Create: `app/handlers/stock.py`
- Create: `app/handlers/orders.py`
- Create: `app/handlers/forward.py`
- Create: `app/handlers/help.py`
- Create: `app/handlers/llm_fallback.py`

- [ ] **Step 1: Create `app/handlers/__init__.py`**

Empty file.

- [ ] **Step 2: Create `app/handlers/sales.py`**

```python
from app.sheets import get_today_sales, get_monthly_sales


def handle_sales_today() -> str:
    return get_today_sales()


def handle_sales_month() -> str:
    return get_monthly_sales()
```

- [ ] **Step 3: Create `app/handlers/stock.py`**

```python
import re
from app.sheets import get_stock


def handle_stock(text: str) -> str:
    """Parse 'stock [product]' and return stock info."""
    match = re.match(r"stock\s+(.+)", text, re.IGNORECASE)
    if not match:
        return "ใช้คำสั่ง: stock [ชื่อสินค้า] เช่น stock แป้งผีเสื้อ"
    product = match.group(1).strip()
    return get_stock(product)
```

- [ ] **Step 4: Create `app/handlers/orders.py`**

```python
from app.sheets import get_today_orders


def handle_orders_today() -> str:
    return get_today_orders()
```

- [ ] **Step 5: Create `app/handlers/forward.py`**

```python
import re
from app.database import get_forward_target
from app.line_bot import push_message, push_group_message
from app.config import settings


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
        push_group_message(group_id, message)
        return "ส่งข้อความถึงกลุ่มแล้ว"

    user_id = get_forward_target(target)
    if not user_id:
        return f"ไม่พบ '{target}' ในรายชื่อผู้รับ ส่งייןแอดมินเพื่อเพิ่ม"

    push_message(user_id, message)
    return f"ส่งข้อความถึง {target} แล้ว"
```

- [ ] **Step 6: Create `app/handlers/help.py`**

```python
HELP_TEXT = """คำสั่งที่ใช้ได้:
ยอดวันนี้ - ดูยอดขายวันนี้
ยอดเดือนนี้ - ดูยอดขายเดือนนี้
stock [สินค้า] - เช็คสต็อกสินค้า
ออเดอร์วันนี้ - ดูออเดอร์วันนี้
/send [ชื่อ] [ข้อความ] - ส่งข้อความถึงคนนั้น
/send group [ข้อความ] - ส่งข้อความถึงกลุ่ม
help - แสดงคำสั่ง"""


def handle_help() -> str:
    return HELP_TEXT
```

- [ ] **Step 7: Create `app/handlers/llm_fallback.py`**

```python
from app.database import get_config


def handle_fallback(text: str) -> str:
    """Fallback when no command matches. Optionally uses LLM."""
    api_key = get_config("llm_api_key") or ""
    if not api_key:
        return "ไม่เข้าใจคำสั่งค่ะ พิมพ์ 'help' เพื่อดูคำสั่งที่มี"

    # Simple fallback without LLM for now
    return "ไม่เข้าใจคำสั่งค่ะ พิมพ์ 'help' เพื่อดูคำสั่งที่มี"
```

- [ ] **Step 8: Create `app/handlers/router.py`**

```python
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
```

- [ ] **Step 9: Commit**

```bash
git add app/handlers/
git commit -m "feat: add command router and all message handlers"
```

---

### Task 6: Main FastAPI app (webhook + alert endpoints)

**Files:**
- Create: `app/main.py`
- Create: `app/models.py`

- [ ] **Step 1: Create `app/models.py`**

```python
from pydantic import BaseModel
from typing import Any


class LineEvent(BaseModel):
    """Simplified LINE webhook event."""
    type: str
    replyToken: str | None = None
    message: dict[str, Any] | None = None
    source: dict[str, Any] | None = None


class LineWebhookPayload(BaseModel):
    """LINE webhook request body."""
    events: list[dict[str, Any]] = []
```

- [ ] **Step 2: Create `app/main.py`**

```python
import json
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.line_bot import verify_signature, reply_message
from app.database import log_message
from app.handlers.router import route_message

app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def line_webhook(request: Request):
    """LINE webhook entry point."""
    # Read raw body
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Line-Signature")
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse events
    payload = json.loads(body)
    events = payload.get("events", [])

    for event in events:
        event_type = event.get("type")
        if event_type != "message":
            continue

        message = event.get("message", {})
        message_type = message.get("type")
        reply_token = event.get("replyToken")
        user_id = event.get("source", {}).get("userId")
        group_id = event.get("source", {}).get("groupId")

        if message_type == "text":
            user_text = message.get("text", "")
            # Route to handler
            reply_text = route_message(user_text, group_id)
            # Send reply
            try:
                reply_message(reply_token, reply_text)
            except Exception as e:
                print(f"Reply error: {e}")
            # Log
            log_message(user_id, user_text, reply_text)

    return JSONResponse(content={"status": "ok"})


@app.post("/alert-check")
async def alert_check(request: Request):
    """Endpoint called by Hermes cron to evaluate alert thresholds."""
    # Placeholder for future alert logic
    return JSONResponse(content={"status": "checked", "alerts": []})
```

- [ ] **Step 3: Create `run.py`** at project root

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 4: Commit**

```bash
git add app/main.py app/models.py run.py
git commit -m "feat: add FastAPI app with webhook and alert endpoints"
```

---

### Task 7: Deploy config (requirements + Railway)

**Files:**
- Create: `requirements.txt`
- Create: `runtime.txt` (for Railway Python version)
- Modify: `.env.example` (already created)

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic-settings==2.7.1
supabase==2.9.0
line-bot-sdk==3.14.0
google-api-python-client==2.161.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.1
python-dotenv==1.0.1
```

- [ ] **Step 2: Create `runtime.txt`**

```
python-3.11
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt runtime.txt
git commit -m "chore: add deployment config"
```

---

### Task 8: Final verification

- [ ] **Step 1: Verify imports work**

```bash
cd /c/Users/Kawin05/Desktop/line-team-bot
pip install -r requirements.txt
python -c "from app.config import settings; print('Config OK')"
python -c "from app.handlers.router import route_message; print(route_message('help')); print('Router OK')"
```

- [ ] **Step 2: Commit any fixes**

```bash
git add -A
git commit -m "chore: final adjustments after verification"
```
