import json
import os
from openai import OpenAI
from app.config import settings

SYSTEM_PROMPT = """คุณคือบอทช่วยงานทีมของร้านค้าออนไลน์
- ตอบเป็นภาษาไทย สั้น กระชับ ไม่เกิน 3 ประโยค
- ใช้ภาษาเป็นกันเอง เป็นธรรมชาติ คุยเหมือนเพื่อนร่วมงาน
- ถามเกี่ยวกับยอดขาย สินค้าคงคลัง หรือออเดอร์ ให้ตอบด้วยข้อมูล
- คุยเรื่องทั่วไปได้ ถามสารทุกข์สุกดิบ เล่าเรื่องขำๆ ได้
- ถ้าไม่รู้คำตอบ ให้บอกว่าไม่รู้และแนะนำให้ถามแอดมิน"""

MAX_HISTORY = 10
HISTORY_DIR = "data/conversations"


def _get_history_path(user_id: str) -> str:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    return os.path.join(HISTORY_DIR, f"{user_id}.json")


def _load_history(user_id: str) -> list:
    path = _get_history_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_history(user_id: str, history: list):
    path = _get_history_path(user_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history[-MAX_HISTORY:], f, ensure_ascii=False)
    except OSError:
        pass  # silently fail on write error


def get_client() -> OpenAI | None:
    if not settings.LLM_API_KEY:
        return None
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )


def handle_fallback(text: str, user_id: str = "") -> str:
    """Fallback when no command matches. Uses LLM with conversation history."""
    client = get_client()
    if not client:
        return "ไม่เข้าใจคำสั่งค่ะ พิมพ์ 'help' เพื่อดูคำสั่งที่มี"

    history = _load_history(user_id) if user_id else []
    history.append({"role": "user", "content": text})

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            max_tokens=200,
            temperature=0.7,
        )
        reply = response.choices[0].message.content or "ขอโทษค่ะ ไม่เข้าใจ กรุณาลองถามใหม่นะคะ"
        history.append({"role": "assistant", "content": reply})
        _save_history(user_id, history)
        return reply
    except Exception as e:
        print(f"[llm] API error: {e}")
        return "ขอโทษค่ะ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
