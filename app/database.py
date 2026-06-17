from functools import cache

from supabase import create_client, Client
from app.config import settings


@cache
def get_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def get_config(key: str) -> str | None:
    """Read a bot_config value by key."""
    try:
        result = get_client().table("bot_config").select("value").eq("key", key).execute()
        if result.data:
            return result.data[0].get("value")
        return None
    except Exception as e:
        print(f"[database] get_config error: {e}")
        return None


def log_message(user_id: str, command: str | None, reply: str | None):
    """Log a message exchange."""
    try:
        get_client().table("message_logs").insert({
            "user_id": user_id,
            "command": command,
            "reply": reply
        }).execute()
    except Exception as e:
        print(f"[database] log_message error: {e}")


def get_forward_target(name: str) -> str | None:
    """Get LINE user ID for a forward target by name."""
    try:
        result = get_client().table("forward_targets").select("line_user_id").eq("name", name).execute()
        if result.data:
            return result.data[0].get("line_user_id")
        return None
    except Exception as e:
        print(f"[database] get_forward_target error: {e}")
        return None
