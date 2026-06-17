import hashlib
import hmac
import base64
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage, PushMessageRequest
)
from linebot.v3.messaging import ApiException
from app.config import settings

configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)


def verify_signature(body: bytes, signature: str | None) -> bool:
    """Verify LINE webhook signature using HMAC-SHA256."""
    if not signature:
        return False
    hash_digest = hmac.new(
        settings.LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    computed = base64.b64encode(hash_digest).decode("utf-8")
    return hmac.compare_digest(computed, signature)


def reply_message(reply_token: str, text: str) -> bool:
    """Reply to a LINE message by reply token. Returns True on success."""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
        return True
    except ApiException as e:
        print(f"[line_bot] reply_message error: {e}")
        return False


def push_message(to_id: str, text: str) -> bool:
    """Push a message to a LINE user or group. Returns True on success."""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=to_id,
                    messages=[TextMessage(text=text)]
                )
            )
        return True
    except ApiException as e:
        print(f"[line_bot] push_message error: {e}")
        return False
