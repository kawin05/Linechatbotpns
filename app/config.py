from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LINE
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS: str = ""  # JSON string or path
    SALES_SHEET_ID: str = ""
    STOCK_SHEET_ID: str = ""
    ORDERS_SHEET_ID: str = ""

    # LLM Fallback (optional)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://opencode.ai/zen/go/v1"
    LLM_MODEL: str = "deepseek-v4-flash"

    # App
    PROJECT_NAME: str = "LINE Team Bot"

    class Config:
        env_file = ".env"


settings = Settings()
