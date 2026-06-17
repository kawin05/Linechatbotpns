from openai import OpenAI
from app.config import settings

SYSTEM_PROMPT = """คุณคือบอทช่วยงานทีมขายของร้านค้าออนไลน์
- ตอบเป็นภาษาไทย สั้น กระชับ ไม่เกิน 3 ประโยค
- ใช้ภาษาเป็นกันเอง แต่สุภาพ
- ถามเกี่ยวกับยอดขาย สินค้าคงคลัง หรือออเดอร์ ให้ตอบสั้นๆ
- ถ้าไม่ใช่เรื่องงาน บอกว่าไม่เข้าใจและแนะนำให้พิมพ์ help"""


def get_client() -> OpenAI | None:
    if not settings.LLM_API_KEY:
        return None
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )


def handle_fallback(text: str) -> str:
    """Fallback when no command matches. Uses LLM if configured."""
    client = get_client()
    if not client:
        return "ไม่เข้าใจคำสั่งค่ะ พิมพ์ 'help' เพื่อดูคำสั่งที่มี"

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[llm] API error: {e}")
        return "ขอโทษค่ะ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
