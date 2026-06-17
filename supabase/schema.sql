-- Team members (who can use the bot)
CREATE TABLE IF NOT EXISTS team_members (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  line_user_id TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Forward targets (who can receive DMs)
CREATE TABLE IF NOT EXISTS forward_targets (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  line_user_id TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Message logs
CREATE TABLE IF NOT EXISTS message_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  command TEXT,
  reply TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bot config (key-value for system prompt, thresholds, sheet IDs)
CREATE TABLE IF NOT EXISTS bot_config (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value TEXT NOT NULL
);

-- Seed default system prompt
INSERT INTO bot_config (key, value) VALUES ('system_prompt', 'คุณคือบอทช่วยงานทีมขายของ Kawin05
- ตอบเป็นภาษาไทย สั้น กระชับ ไม่เกิน 3 ประโยค
- ใช้ภาษาเป็นกันเอง แต่สุภาพ
- ถ้าไม่เข้าใจคำสั่ง ให้บอกว่าไม่เข้าใจและแนะนำให้พิมพ์ help') ON CONFLICT (key) DO NOTHING;
