import hashlib
import hmac
import base64
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
