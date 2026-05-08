# Jobs: Chinese Internet Fixed Expression Search Engine

This document lists implementation tasks for building a platform that helps users quickly search for and reuse fixed sentence patterns (固定句式) popular on Chinese social media, especially Bilibili. The system crawls, extracts, and serves these patterns via a search interface.

Tech stack:
- Frontend: Next.js (React)
- Backend: Python (FastAPI)
- Database: PostgreSQL (with pgvector extension for vector search if needed)
- Deployment: Railway

## Phase 1: Project Initialization & Database Schema

### Job 1.1: Initialize Repositories and Project Structure
- Set up a monorepo with `/frontend` (Next.js with TypeScript) and `/backend` (Python with FastAPI).
- Initialize a Railway project, attach a PostgreSQL database, and note connection strings.
- Configure environment variables: `DATABASE_URL`, `CORS_ORIGINS`, `SECRET_KEY`, `OPENAI_API_KEY` (optional for LLM tasks), etc.
- Create basic lint and format configs, README.

### Job 1.2: Design and Create Database Tables
- Write SQL migration scripts (or use SQLAlchemy/Alembic) for the following tables:
  - `raw_texts`: stores scraped sentences with metadata (source URL, platform, timestamp, raw content, type: comment/danmaku/post).
  - `sentence_patterns`: extracted patterns (template text, POS sequence, associated tags, source_count, created_at).
  - `pattern_examples`: example real-world usage linking a pattern to a raw_text, with slot fillings stored as JSON (e.g., {"key1": "社会主义", "key2": "救中国"}).
  - `tags`: tag name, category (domain/sentiment/style).
  - `pattern_tags`: many-to-many relation.
  - `search_logs` (optional): log user queries for future improvement.
- Include database indexes: full-text search index on `sentence_patterns.template`, GIN index on tags, trigram index for fuzzy matching if needed.
- Provide a script to initialize the database schema.

## Phase 2: Data Collection & Cleaning

### Job 2.1: Bilibili Comment/Danmaku Crawler
- Implement a Python module `crawlers/bilibili.py` using `httpx` or `aiohttp`.
- Respect Bilibili API rate limits; use per-video endpoint for comments (`api.bilibili.com/x/v2/reply`) and danmaku (protobuf or XML endpoint).
- Accept a list of BV numbers or a dynamic discovery method (e.g., trending videos) via config.
- Store crawled data into `raw_texts`, deduplicate by content hash.
- Add a simple CLI command: `python -m crawlers.bilibili --bvs BV1xx411c7mD ...`

### Job 2.2: Multi-Platform Crawler (Weibo, Zhihu, Tieba)
- Extend with adapters for Weibo, Zhihu, Tieba, etc., using their public APIs or static HTML where legally allowed.
- Implement a unified pipeline: fetch → clean (remove emojis, HTML tags) → store.
- Ensure polite crawling: random delays, respect `robots.txt`.

### Job 2.3: Scheduling & Incremental Crawling
- Set up a background task scheduler (e.g., `APScheduler` or a simple loop) to run crawlers periodically.
- Log crawl statistics (success, duplicates, errors).

## Phase 3: NLP & Pattern Extraction Pipeline

### Job 3.1: Rule-Based Pattern Extraction
- Use `jieba` with POS tagging (or `LTP`/`HanLP`) to tokenize and tag sentences.
- Define templates for common Chinese connectives: "只有...才...", "虽然...但是...", "既然...那就...", etc.
- Scan raw texts for such frames, convert to patterns with POS wildcards.
- Store extracted patterns and link to examples (`pattern_examples`).
- Create a set of initial domain-specific dictionaries (e.g., political jargon, slang) for tagging.

### Job 3.2: Semantic Clustering & Pattern Discovery (AI)
- Use `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) to encode all raw sentences.
- Cluster similar sentences (via `faiss` or `scikit-learn`) to discover semantically identical but lexically varied patterns.
- For each cluster, generate a canonical template using a heuristic (most frequent POS sequence) or by sending a sample to an LLM (DeepSeek/ChatGPT) with a prompt: "Extract the shared template with placeholders from these sentences: ..."
- Store new patterns and link underlying examples.

### Job 3.3: Automated Tagging
- Apply keyword matching (using the domain dictionaries) and small classifier (e.g., logistic regression on embeddings) to assign tags like `#建政`, `#阴阳怪气`, `#手游`, etc.
- Update pattern_tags accordingly.

### Job 3.4: NLP Pipeline Orchestration
- Build a pipeline script that runs extraction, clustering, and tagging on new raw data incrementally.
- Provide a CLI: `python -m nlp.run_pipeline --since yesterday`.

## Phase 4: Backend API Development

### Job 4.1: Core Search API
- Create FastAPI endpoints:
  - `GET /api/search?q=只有...才...&page=1&size=20`
    - Accept template fragment, full regex-style pattern, or keywords.
    - Handle fuzzy matching: if query contains "*", convert to SQL LIKE or to `pg_trgm` similarity search.
    - If query is plain text, perform full-text search on `pattern_examples.content` and return associated pattern.
  - `GET /api/patterns/{id}`: retrieve pattern with examples, tags, and usage stats.
  - `GET /api/patterns/{id}/generate?key1=xxx&key2=yyy`: fill the pattern with user-provided slots and return generated sentence(s).
  - `GET /api/tags`: list tags with counts.
  - `GET /api/examples?pattern_id=...&sort=hot`: paginated examples.

### Job 4.2: Ranking & Trending
- Implement a scoring function: combine recency, frequency, upvote count (if available), and user click logs.
- Endpoint: `GET /api/trending` returns top patterns by time range.

### Job 4.3: Search Intent Recognition (Optional Enhancement)
- Add a lightweight classifier (or LLM-based) to map freeform user input (e.g., "表达无奈的古风句式") to structured parameters: `type=emotional_expression, style=classical`.
- Use LLM prompt in backend: "Classify the user intent into a structured JSON: ..." and then translate to a database query.

### Job 4.4: Admin Endpoints (if needed)
- `POST /api/admin/crawl/trigger`: trigger a crawl job manually.
- `GET /api/admin/stats`: overview of stored patterns, examples, crawl status.

## Phase 5: Frontend Implementation

### Job 5.1: Next.js App Setup and Routing
- Set up pages: `/` (home/search), `/pattern/[id]`, `/browse`, `/museum`.
- Use `shadcn/ui` or Tailwind CSS for styling.
- Create a reusable API client (axios/fetch) in `lib/api.ts`.

### Job 5.2: Search Interface (Home Page)
- Smart search bar with auto-suggestions (debounced API calls to `/api/search?suggest=...`).
- Allow input of both Chinese text and wildcards (e.g., "只有*才*").
- Results display as cards: pattern template, one highlighted example, tags, number of examples. Click to expand / navigate to detail page.
- Filter sidebar: tags, platform, time range.

### Job 5.3: Pattern Detail Page & Interactive Generator
- Show pattern template, all examples, tag list.
- Interactive "Fill & Generate" widget: input fields appear based on slot variables (extracted from pattern), user enters words, generative result updates in real time via `/api/patterns/{id}/generate`.
- "Copy to clipboard" button for generated sentence.

### Job 5.4: Museum / Discovery Page
- Grid display of curated "神评模板" with nice typography.
- Sorting options: newest, most copied, staff picks.

### Job 5.5: Responsive Design & SEO
- Ensure mobile-friendly layout.
- Add meta tags, Open Graph, and basic SSR for pattern pages to allow social sharing.

## Phase 6: Deployment & Monitoring

### Job 6.1: Railway Configuration
- Add `railway.json` or configure services via dashboard:
  - Frontend service: `cd frontend && npm run build && npm start`
  - Backend service: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set environment variables in Railway (DATABASE_URL, etc.).

### Job 6.2: Database Migration on Deploy
- Run Alembic migrations automatically on backend startup or via a Railway pre-deploy script.

### Job 6.3: Health Checks & Logging
- Add `/health` endpoint to FastAPI that checks DB connectivity.
- Configure Railway health checks.
- Integrate basic logging (stdout) and verify logs appear in Railway logs.

### Job 6.4: Cron Job for Data Pipeline
- Set up a Railway cron job (or a separate service) to run `python -m nlp.run_pipeline` daily to process new raw texts.

## Additional Notes
- All crawling must be respectful and follow robots.txt. Include a `User-Agent` header identifying your project with a contact email.
- For LLM-powered features (like pattern extraction or intent classification), use environment variable for the API key and implement a fallback to rule-based methods if unavailable.
- Use asynchronous Python (FastAPI with asyncpg) for high concurrency.
- Keep state minimal on frontend; rely on URL query params for search state to allow easy sharing.