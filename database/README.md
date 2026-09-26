# TARA Database & Persistence Layer

This directory serves as the placeholder and storage directory for the **TARA** conversation persistence layer.

---

## Architecture Overview

TARA uses a decoupled **Repository Pattern** defined in `backend/db/repository.py`. The chatbot application logic interacts exclusively with the `BaseConversationRepository` interface, ensuring zero hardcoding of database-specific queries in intent classification or response generation.

```
                    ┌─────────────────────────┐
                    │  TARA Prediction Engine  │
                    └───────────┬─────────────┘
                                │
                                ▼
                   ┌───────────────────────────┐
                   │ BaseConversationRepository │
                   └─────────────┬─────────────┘
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ InMemory (Dev)   │   │ SQLite (File)    │   │ PostgreSQL/Mongo │
│ DB_TYPE=memory   │   │ DB_TYPE=sqlite   │   │ (Plug-and-play)  │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 1. Expected Database Schema

### Table: `messages`
Stores user queries, recognized speech transcripts, detected Deep Learning intents, confidence scores, and assistant responses.

| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR(64)` PRIMARY KEY | Unique message UUID |
| `session_id` | `VARCHAR(64)` INDEXED | Conversation session identifier |
| `role` | `VARCHAR(16)` | `"user"` or `"assistant"` or `"system"` |
| `content` | `TEXT` | Raw text or recognized speech / bot response |
| `intent` | `VARCHAR(64)` NULLABLE | DL-predicted intent tag (e.g., `ai_concepts`, `greeting`) |
| `confidence` | `REAL` NULLABLE | Intent prediction softmax probability (0.0 – 1.0) |
| `sentiment` | `VARCHAR(16)` NULLABLE | Sentiment polarity (`POSITIVE`, `NEUTRAL`, `NEGATIVE`) |
| `timestamp` | `DOUBLE PRECISION` | Epoch timestamp in seconds |

### Table: `session_topics`
Tracks the active context entity for conversational follow-ups (e.g. resolving pronouns like *"What are its types?"*).

| Column | Type | Description |
|---|---|---|
| `session_id` | `VARCHAR(64)` PRIMARY KEY | Session UUID |
| `last_topic` | `VARCHAR(64)` | Most recent subject / intent |
| `updated_at` | `DOUBLE PRECISION` | Timestamp of last topic update |

---

## 2. Environment Variables

Configure these environment variables in your `.env` or deployment environment (Render, Railway, Vercel):

| Variable | Values | Default | Description |
|---|---|---|---|
| `DB_TYPE` | `memory` \| `sqlite` \| `postgres` \| `mongodb` | `memory` | Selected database storage engine |
| `DATABASE_URL` | Connection URI | `""` | Database connection string (e.g., `sqlite:///database/tara.db`, `postgresql://user:pass@host:5432/taradb`) |
| `SQLITE_PATH` | File path | `database/tara_conversations.db` | Local SQLite file path when using SQLite |

---

## 3. Switching From Development to Production Database

### Option A: Use Persistent SQLite (Default Production File DB)
1. Set in `.env`:
   ```env
   DB_TYPE=sqlite
   SQLITE_PATH=database/tara_conversations.db
   ```
2. The database file and tables will be auto-created upon the first request.

### Option B: Connect to PostgreSQL / MySQL
1. Install driver:
   ```bash
   pip install psycopg2-binary sqlalchemy
   ```
2. Implement `PostgresConversationRepository(BaseConversationRepository)` in `backend/db/repository.py`.
3. Set environment variable:
   ```env
   DB_TYPE=postgres
   DATABASE_URL=postgresql://username:password@ep-host.aws.neon.tech/taradb?sslmode=require
   ```

### Option C: Connect to MongoDB
1. Install motor/pymongo:
   ```bash
   pip install pymongo
   ```
2. Implement `MongoConversationRepository(BaseConversationRepository)` in `backend/db/repository.py`.
3. Set environment variable:
   ```env
   DB_TYPE=mongodb
   DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/taradb?retryWrites=true&w=majority
   ```

---

## 4. How Conversation History & Context Are Persisted

1. **Incoming Request**: When user sends a message (voice or text), frontend passes a `session_id`.
2. **Context Resolution**: The predictor retrieves the last discussed topic via `repo.get_last_topic(session_id)`.
3. **Response Generation**: The user message and TARA response are atomically stored with `repo.save_message(record)`.
4. **Session Retrieval**: Frontend or external audit tools can fetch history anytime via `GET /history?session_id=<ID>`.
