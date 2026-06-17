from pydantic import BaseModel
from typing import Any


class LineWebhookPayload(BaseModel):
    events: list[dict[str, Any]] = []
