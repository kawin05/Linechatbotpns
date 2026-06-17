# LINE OA Team Bot — Design Spec

**Date:** 2026-06-17
**Status:** Draft
**Project:** line-team-bot

---

## Overview

A LINE Official Account bot for Kawin05's e-commerce team. Lives in the team LINE group. Team members query sales, stock, and orders. Kawin05 can push messages to specific people or the group. Auto-alerts fire on data thresholds.

---

## Architecture

```
LINE Group / LINE User
       │ Webhook events
       ▼
FastAPI Server (Railway / VPS)
       │
       ├──→ Supabase (team_members, forward_targets, message_logs, bot_config)
       │
       └──→ Google Sheets API (Sales, Stock, Orders)
```

### Components

| Component | Responsibility |
|---|---|
| Webhook Receiver | Accepts LINE events, validates signature |
| Message Handler | Parses incoming text, routes to command handler or LLM fallback |
| Command Router | Pattern-matches known commands → Sheets queries |
| LLM Fallback | When command not recognized → forward to LLM for natural reply |
| Forward Service | Sends messages to specific LINE users or the group |
| Alert Scheduler | Periodic check on data thresholds → push notifications |

---

## Message Flow

```
Team member: "ยอดวันนี้"
  → LINE webhook → FastAPI
    → Command Router: match "ยอดวันนี้"
      → Google Sheets API: read today's total from Sales sheet
      → Format: "ยอดขายวันนี้ ฿XX,XXX (XX ออเดอร์)"
      → LINE Reply API → group

Team member: "ส่งของถึงลูกค้ายัง"
  → No command match
    → LLM Fallback: "ขอโทษค่ะ ไม่เข้าใจคำถาม กรุณาพิมพ์ 'help' เพื่อดูคำสั่งที่มี"
    → LINE Reply API → group
```

---

## Commands

| Command | Handler | Source |
|---|---|---|
| `ยอดวันนี้` | Sales handler | Google Sheet |
| `ยอดเดือนนี้` | Sales handler | Google Sheet |
| `stock [product]` | Stock handler | Google Sheet |
| `ออเดอร์วันนี้` | Orders handler | Google Sheet |
| `/send [name] [msg]` | Forward service | — |
| `/send group [msg]` | Forward service | — |
| `help` | Help handler | — |
| `*anything else*` | LLM fallback | Uses configured LLM provider (env var). Falls back to "ไม่เข้าใจคำสั่ง" response if no LLM key set. |

---

## Data Models

### Supabase: `team_members`
```sql
CREATE TABLE team_members (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  line_user_id TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'member',  -- 'member' | 'admin'
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Supabase: `forward_targets`
```sql
CREATE TABLE forward_targets (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  line_user_id TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Supabase: `message_logs`
```sql
CREATE TABLE message_logs (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  command TEXT,
  reply TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Supabase: `bot_config`
```sql
CREATE TABLE bot_config (
  id SERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value TEXT
);
-- Seed: INSERT INTO bot_config (key, value) VALUES ('system_prompt', '...');
```

---

## Google Sheets Integration

Three sheets, read via Google Sheets API (service account):

| Sheet | Purpose | Used by commands |
|---|---|---|
| Sales Sheet | Daily revenue, total, orders count | `ยอดวันนี้`, `ยอดเดือนนี้` |
| Stock Sheet | Product name + remaining units | `stock [product]` |
| Orders Sheet | Recent orders with status | `ออเดอร์วันนี้` |

Sheet IDs and range names stored in `bot_config` table for zero-code reconfiguration.

---

## Bot Identity

Stored as `system_prompt` in `bot_config`. Loaded on every request. Editable anytime — behavior changes instantly.

---

## Scheduler & Alerts

Uses **Hermes cron** — already working, no extra infra. Cron job fires at configured times, hits FastAPI endpoint `/alert-check` to evaluate thresholds, returns alert messages.

Alert types:
- Sales below daily target
- Stock low (below configurable threshold)
- New orders in the last hour

Configurable thresholds stored in `bot_config` table.

---

## Deployment

| Service | What for | Cost |
|---|---|---|
| Railway | FastAPI server | Free tier |
| Supabase | Database | Free tier |
| Google Cloud | Sheets API | Free quota |
| LINE Developers | Messaging API channel | Free |

### Setup Steps (one-time)

1. Create LINE Messaging API channel → get Channel Secret + Access Token
2. Create Supabase project → run schema SQL
3. Google Cloud → enable Sheets API → create service account → share sheets
4. Push FastAPI code to GitHub → Railway auto-deploys
5. Set LINE webhook URL to `https://<railway-url>/webhook`
6. Seed `forward_targets` and `team_members` tables

---

## Files

```
line-team-bot/
├── app/
│   ├── main.py              # FastAPI app, webhook endpoint
│   ├── config.py            # Settings (env vars)
│   ├── database.py          # Supabase client
│   ├── sheets.py            # Google Sheets reader
│   ├── handlers/
│   │   ├── sales.py         # ยอดวันนี้, ยอดเดือนนี้
│   │   ├── stock.py         # stock [product]
│   │   ├── orders.py        # ออเดอร์วันนี้
│   │   ├── forward.py       # /send
│   │   ├── help.py          # help
│   │   └── llm_fallback.py  # fallback to LLM
│   └── models.py            # Pydantic schemas
├── supabase/
│   └── schema.sql           # Table DDL
├── requirements.txt
└── docs/
    └── superpowers/specs/2026-06-17-line-oa-team-bot-design.md
```
