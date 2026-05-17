# JuShi (句式) — Searchable Chinese Intertextual Sentence Frames

`JuShi` here does not mean any generic sentence pattern.

It means a sentence structure people remember because of an original, iconic moment:
someone said it, an event fixed it in memory, and later people replace the nouns,
verbs, or other slots while the audience still recalls that original moment.

That is the product idea this repo is moving toward.

## Product Definition

A good `JuShi` has three parts:

1. An original memorable utterance or scene.
2. A reusable sentence frame that survives slot substitution.
3. A recall effect: when the frame is reused, people can still infer or remember the
   original event being referenced.

Examples of what the system should eventually help users do:

- Search a known frame like `感谢*让我*`
- Discover related variants and drifted versions of the same frame
- Inspect example usages across platforms
- Understand what original moment or earlier meme made the frame recognizable

## What The Repo Does Today

Today the codebase already supports the lower layers of that idea:

- Crawl raw Chinese internet text from platforms such as Bilibili
- Extract reusable sentence templates with slot placeholders
- Store examples, tags, variants, and usage counts
- Search and browse templates in a Next.js frontend

In other words, the repo already indexes reusable sentence structures, but it only
partially captures the stronger `JuShi` idea of "this frame makes people remember that
specific original moment."

## Current Product Gap

The main gap is provenance.

The current schema stores:

- `sentence_patterns`
- `pattern_examples`
- `tags`
- canonical / variant relations

But it does not yet model the most important `JuShi` layer explicitly:

- the original moment
- the original quote or canonical utterance
- why later substitutions still point back to that source
- confidence that a pattern is truly intertextual, not just syntactically reusable

That means the repo is currently closer to a "fixed expression search engine" than a
full `JuShi` archive.

See [JUSHI_CONCEPT.md](/home/dronelab/Documents/jushu/JUSHI_CONCEPT.md) for the
working definition and recommended next implementation steps.

## Tech Stack

- Frontend: Next.js 14, React, TypeScript, Tailwind CSS
- Backend: Python 3.12, FastAPI, asyncpg, SQLAlchemy
- Database: PostgreSQL with trigram / FTS support
- Deployment: Railway

## Monorepo Structure

```text
jushu/           # repo directory name kept for now
├── frontend/    # Next.js app
├── backend/     # FastAPI app + crawlers + NLP pipeline
└── railway.json # Railway config
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
- `NLP_PIPELINE_CRON`: process unprocessed `raw_texts` into patterns / examples / tags

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

- `GET /api/admin/scheduler` - inspect registered jobs
- `POST /api/admin/scheduler/crawl-now` - run scheduled crawl immediately
- `POST /api/admin/scheduler/pipeline-now` - run scheduled pipeline immediately

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
railway link
railway up
```
