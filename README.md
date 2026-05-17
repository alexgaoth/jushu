# 句式 (Jushu) — Chinese Internet Fixed Expression Search Engine

A platform for searching and reusing fixed sentence patterns (固定句式) popular on Chinese social media, especially Bilibili.

## Tech Stack
- **Frontend**: Next.js 14 (React, TypeScript, Tailwind CSS)
- **Backend**: Python 3.12 (FastAPI, asyncpg, SQLAlchemy)
- **Database**: PostgreSQL (with pg_trgm for fuzzy search)
- **Deployment**: Railway

## Monorepo Structure
```
jushu/
├── frontend/     # Next.js app
├── backend/      # FastAPI app
└── railway.json  # Railway config
```

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # fill in DATABASE_URL
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Scheduled Scraping
The API can launch scraping in three ways:

- Manual CLI: `python -m crawlers.bilibili --keywords 社会热点 时事吐槽 网络热梗`
- Manual API trigger: `POST /api/admin/crawl/trigger`
- App scheduler on startup: enable `SCRAPER_SCHEDULER_ENABLED=true` in `backend/.env`

When the scheduler is enabled, the backend registers two cron jobs at startup:

- `BILIBILI_CRAWL_CRON`: keyword-based Bilibili crawl
- `NLP_PIPELINE_CRON`: process unprocessed `raw_texts` into patterns/examples/tags

Relevant env vars:
```bash
SCRAPER_SCHEDULER_ENABLED=true
SCRAPER_SCHEDULE_TIMEZONE=UTC
BILIBILI_CRAWL_CRON="0 3 * * *"
NLP_PIPELINE_CRON="20 3 * * *"
BILIBILI_SCHEDULED_KEYWORDS='["社会热点","时事吐槽","网络热梗"]'
BILIBILI_SCHEDULED_KEYWORD_RESULTS=10
```

Operational endpoints:

- `GET /api/admin/scheduler` — inspect registered jobs
- `POST /api/admin/scheduler/crawl-now` — run scheduled crawl immediately
- `POST /api/admin/scheduler/pipeline-now` — run scheduled pipeline immediately

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL
npm run dev
```

## Railway Deployment
```bash
railway login
railway link     # link to your Railway project
railway up
```
