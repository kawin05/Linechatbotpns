import json
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.line_bot import verify_signature, reply_message
from app.database import log_message
from app.handlers.router import route_message

# Temp: capture group IDs for setup
_last_events = []

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
    t0 = time.perf_counter()

    body = await request.body()
    t1 = time.perf_counter()

    signature = request.headers.get("X-Line-Signature")
    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    t2 = time.perf_counter()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    t3 = time.perf_counter()

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
        source_type = event.get("source", {}).get("type")

        # Temp: capture event for debug
        _last_events.append({"sourceType": source_type, "groupId": group_id, "userId": user_id, "ts": time.time()})
        if len(_last_events) > 20:
            _last_events.pop(0)

        if message_type == "text":
            user_text = message.get("text", "")
            t4 = time.perf_counter()
            reply_text = route_message(user_text, group_id, user_id)
            t5 = time.perf_counter()
            reply_message(reply_token, reply_text)
            t6 = time.perf_counter()
            try:
                log_message(user_id, user_text, reply_text)
            except Exception:
                pass
            t7 = time.perf_counter()

            print(
                f"[TIMING] read_body={t1-t0:.3f}s  "
                f"verify_sig={t2-t1:.3f}s  "
                f"parse_json={t3-t2:.3f}s  "
                f"route+handler={t5-t4:.3f}s  "
                f"line_reply={t6-t5:.3f}s  "
                f"supabase_log={t7-t6:.3f}s  "
                f"total={t7-t0:.3f}s  "
                f"cmd={user_text[:30]}  "
                f"groupId={group_id or 'none'}  "
                f"userId={user_id or 'none'}"
            )

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


@app.get("/debug/group-ids")
async def debug_group_ids():
    """TEMP: show last seen group/user IDs for setup."""
    return JSONResponse(content={"events": _last_events})
