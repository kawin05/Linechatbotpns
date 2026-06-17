from openai import OpenAI
from app.config import settings

SYSTEM_PROMPT = """คุณคือบอทช่วยงานทีมของร้านค้าออนไลน์
- ตอบเป็นภาษาไทย สั้น กระชับ ไม่เกิน 3 ประโยค
- ใช้ภาษาเป็นกันเอง เป็นธรรมชาติ คุยเหมือนเพื่อนร่วมงาน
- ถามเกี่ยวกับยอดขาย สินค้าคงคลัง หรือออเดอร์ ให้ตอบด้วยข้อมูล
- คุยเรื่องทั่วไปได้ ถามสารทุกข์สุกดิบ เล่าเรื่องขำๆ ได้
- ถ้าไม่รู้คำตอบ ให้บอกว่าไม่รู้และแนะนำให้ถามแอดมิน"""


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
        return response.choices[0].message.content or "ขอโทษค่ะ ไม่เข้าใจ กรุณาลองถามใหม่นะคะ"
    except Exception as e:
        print(f"[llm] API error: {e}")
        return "ขอโทษค่ะ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
