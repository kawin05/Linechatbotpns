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
