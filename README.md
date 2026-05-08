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
