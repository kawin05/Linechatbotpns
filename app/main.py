import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.line_bot import verify_signature, reply_message
from app.database import log_message
from app.handlers.router import route_message

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.PROJECT_NAME, redirect_slashes=False)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
@limiter.limit("30/minute")
async def line_webhook(request: Request):
    """LINE webhook entry point."""
    body = await request.body()

    signature = request.headers.get("X-Line-Signature")
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

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
            reply_text = route_message(user_text, group_id)
            reply_message(reply_token, reply_text)
            try:
                log_message(user_id, user_text, reply_text)
            except Exception:
                pass  # Supabase not configured yet

    return JSONResponse(content={"status": "ok"})


@app.post("/webhook/")
@limiter.limit("30/minute")
async def line_webhook_slash(request: Request):
    """LINE webhook entry point (with trailing slash)."""
    return await line_webhook(request)


@app.post("/alert-check")
@limiter.limit("10/minute")
async def alert_check(request: Request):
    """Endpoint called by Hermes cron to evaluate alert thresholds."""
    return JSONResponse(content={"status": "checked", "alerts": []})
