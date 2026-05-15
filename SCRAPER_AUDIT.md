# Scraper & NLP Pipeline — Forward Audit

## What has been fixed (no longer gaps)

| Fix | Where |
|---|---|
| Text cleaning (emoji, URLs, @mentions, HTML) before hash | `crawlers/base.py:clean_text()` |
| Concurrent BVID crawl with `Semaphore(3)` | `crawlers/bilibili.py:crawl_bvids()` |
| Trending BVID discovery via `/x/web-interface/popular` | `crawlers/bilibili.py:_fetch_trending_bvids()` |
| `seen_templates` dedup removed — all matches captured | `nlp/extractor.py:extract()` |
| POS tagging on actual matched text, not template literal | `nlp/extractor.py` line ~130 |
| Slot regex tightened to `[^。！？\n]{1,20}?` | `nlp/extractor.py:_build_regex()` |
| Chunked pipeline load (`CHUNK = 100`) | `nlp/run_pipeline.py:run_pipeline()` |
| Per-text session — failures can't roll back neighbours | `nlp/run_pipeline.py` |
| Broken texts quarantined (`processed = True`) | `nlp/run_pipeline.py` |

---

## Remaining gaps — path to the ideal state

The target corpus is **political discourse** — not official statements, but how ordinary
Chinese internet users discuss, mock, and reference political events through irony,
historical analogy, and recycled memes. A sentence like 感谢XX让我们YY (thank XX for
making us YY — meaning the opposite) or 这不是第一次了，当年XX也是这样 (this isn't
the first time, XX did the same thing back then) is the core subject matter.

These patterns live in **comment sections and reactions to events**, not in the primary
coverage. The irony is the data, not the news itself.

---

### 1. Corpus is pointed at the wrong content

`_fetch_trending_bvids` pulls the general popular feed. That surface is dominated by
gaming and entertainment. The ironic political discourse we want happens in the comment
sections of:
- Videos that **react to** controversial social or political events (时事评论, 社会热点)
- **History comparison** videos where the implicit argument is the parallel to now (以史为鉴)
- **鬼畜** (meme remix) compilations of political figures or events — these comment
  sections are dense with the exact register we want
- Zhihu answers to "如何看待XX事件" — the answer comment threads, not the answers

Crawling official 时政 channels or 外交部 hashtags gives the primary source, not the
reaction. The 句式 live downstream of the event.

**What is missing:**

**Bilibili keyword search** — `/x/web-interface/search/all?search_type=video&keyword=<kw>`:
Seed keywords that target reaction content and ironic framing, not official coverage:

```
社会热点  网络热梗  时事吐槽  历史对比  这让我想起  感谢让我  评论区  以史为鉴
鬼畜  沙雕时政  懂的都懂  细思极恐  属于是
```

The comment sections on *these* videos are the corpus — not the video text itself.

**Weibo trending topics** — `m.weibo.cn/api/container/getIndex?containerid=<cid>`.
The container IDs for topics like `#网络热梗#`, `#时事吐槽#`, and trending hashtags
around controversial events are publicly accessible. The comments (not the posts) on
these topics carry the ironic sentence patterns. No auth needed for public topics.

**Zhihu** — `www.zhihu.com/api/v4/questions/<id>/answers` with answer comment threads.
Questions of the form "如何看待XX" and "XX是什么感觉" generate answer comment
exchanges where the ironic register is extremely consistent. Public API, no auth.

**Effect of not fixing:** the crawler collects top-of-feed gaming content where ironic
political 句式 are nearly absent.

---

### 2. The 33 connective rules miss the ironic/meme register entirely

The current rules in `nlp/extractor.py:CONNECTIVE_RULES` capture logical connectives
(如果/就, 虽然/但是) in their neutral, sincere use. The ironic discourse we want uses
a different structural vocabulary — frames that signal mock gratitude, feigned surprise,
historical reference, and rhetorical unmasking.

**Patterns to add** (all fit `_build_regex` without infrastructure change):

| Pattern | Real example | Structure |
|---|---|---|
| 感谢X让我Y | 感谢他让我们开了眼界 | `感谢{slot1}让我{slot2}` |
| 多亏了X才Y | 多亏了这个政策我们才能吃到教训 | `多亏了{slot1}才{slot2}` |
| 不愧是X，Y | 不愧是专家，说的都是废话 | `不愧是{slot1}，{slot2}` |
| 原来X，怪不得Y | 原来如此，怪不得他们都不说话 | `原来{slot1}，怪不得{slot2}` |
| 没想到X居然Y | 没想到这个结局居然是这样 | `没想到{slot1}居然{slot2}` |
| 这让我想起了X | 这让我想起了那段历史 | `这让我想起了{slot1}` (one-slot) |
| X的翻版 | 这不是第一次了的翻版 | `{slot1}的翻版` (one-slot) |
| X，懂的都懂 | 某些地方，懂的都懂 | `{slot1}，懂的都懂` (one-slot) |
| X有没有Y的自觉 | 他们有没有基本良知的自觉 | `{slot1}有没有{slot2}的自觉` |
| 就这还X | 就这还想代表我们说话 | `就这还{slot1}` (one-slot) |
| X叫做Y | 这叫做双重标准 | `{slot1}叫做{slot2}` |
| 一方面X，另一方面Y | 一方面喊口号另一方面捞好处 | `一方面{slot1}，另一方面{slot2}` |

**One-slot patterns** require a small change to `_build_regex` — currently it always
generates `slot1` and `slot2`. Add a branch: if `conn_b is None` and the template
contains `{slot1}`, build a one-slot regex with only `(?P<slot1>...)`.

**Existing rules that apply ironically** — no code change needed, but these rules
already capture the ironic register when the corpus is right:
- `要么X，要么Y` (false dilemma framing — common in ironic political commentary)
- `宁可X，也不Y` (principled refusal, often parodied)
- `不是X，而是Y` (unmasking the real reason)
- `与其X，不如Y` (ironic alternative suggestion)

---

### 3. Subvariants — meme drift is not just surface grammar variation

The current scope of "subvariant" is connective-level: 虽然/但是 and 虽然/但 are
the same concessive with different connective_B. That is one type.

The more important type for this corpus is **meme drift** — the same structural
template evolves as it spreads:

- `感谢X让我Y` → `感谢X让我们Y` → `感谢X，让我深刻体会到了Y`
- `不愧是X，Y` → `不愧是X，真的Y` → `不愧是X啊，Y`

These share the same ironic frame but have different surface connectives and slot
boundaries. A pure connective-pair grouping misses them; they look like separate patterns.

**Desired model** (same FK structure as before, but the linking rule changes):
```
sentence_patterns
  canonical_template_id  FK → sentence_patterns.id  (NULL = canonical)
```

**Linking rules:**
1. **Same `conn_a`, different `conn_b`** → subvariant (existing connective logic)
2. **Levenshtein distance ≤ 3 on template strings** → likely meme drift subvariant;
   flag and set `canonical_template_id` pointing to the earlier-created template
3. **Embedding cosine similarity > 0.90 on `sentence-transformers` encodings** →
   confirm as subvariant (longer-term, after clustering infrastructure exists)

Rule 2 is cheap to implement now (stdlib `difflib.SequenceMatcher`) and catches the
drift variants without requiring embeddings.

---

### 4. `PatternExample` has no uniqueness guard

`app/models.py:PatternExample` (lines 91–122) has no `UniqueConstraint` on
`(pattern_id, content)`. With `seen_templates` dedup removed from the extractor,
the same resolved example sentence can be inserted many times across pipeline runs.

**Fix — add to `PatternExample.__table_args__`:**
```python
UniqueConstraint("pattern_id", "content", name="uq_pattern_example_content"),
```
**Fix — change the insert in `run_pipeline.py:process_text`:**
```python
pg_insert(PatternExample)
    .values(...)
    .on_conflict_do_nothing(constraint="uq_pattern_example_content")
```

---

### 5. `source_count` increment is a lost update under concurrency

`run_pipeline.py:process_text` (line ~83) does `pattern.source_count += 1` in
application code — a read-modify-write race if two pipeline processes ever run at
the same time.

**Fix — server-side increment:**
```python
from sqlalchemy import update
await db.execute(
    update(SentencePattern)
    .where(SentencePattern.id == pattern.id)
    .values(source_count=SentencePattern.source_count + 1)
)
```

---

### 6. Tagger is blind to irony and historical reference

`nlp/tagger.py:TAG_DEFINITIONS` already has `阴阳怪气` but its keyword list
(`["阴阳", "讽刺", "挖苦", ...]`) requires the text to *name its own irony*, which
ironic text almost never does. The tag fires on meta-commentary, not on the ironic
句式 themselves.

The tags needed for this corpus are structural and rhetorical, not domain-keyword:

**Add to `TAG_DEFINITIONS`:**
```python
"借古讽今": (
    "style",
    # triggers when historical reference is used to comment on the present
    ["想起了", "当年", "历史", "重演", "翻版", "那时候", "那一年", "不是第一次"],
),
"反向感谢": (
    "style",
    # ironic gratitude — nearly always sarcastic in political discourse
    ["感谢", "多亏了", "要不是", "托了", "幸亏"],
),
"梗引用": (
    "style",
    # recognisable meme frames being recycled
    ["懂的都懂", "不愧是", "属于是", "细思极恐", "就这还", "这波", "绷不住"],
),
"反问讽刺": (
    "style",
    # rhetorical question as sarcasm — already partially covered by 反问句
    # but that tag fires on structure; this one fires on content signal
    ["难道", "凭什么", "居然", "竟然", "有没有", "自觉"],
),
```

**Update `阴阳怪气` keyword list** — the current list fires on meta-labels, not on
the patterns themselves. Replace with words that actually appear *inside* ironic 句式:
```python
"阴阳怪气": (
    "sentiment",
    ["不愧", "原来如此", "怪不得", "没想到", "居然", "看来", "果然", "总算",
     "所谓", "这就是", "真是", "感谢", "幸亏"],
),
```

---

## Recommended implementation order

### Phase 1 — Point the crawler at the right content

1. **`crawlers/bilibili.py`** — add `_search_bvids(keyword, n)` using
   `/x/web-interface/search/all?search_type=video&keyword=<kw>&ps=20&pn=<p>`.
   Add `--keywords` CLI arg that accepts a list, searches each keyword, and merges
   BVIDs (deduped). Use ironic/reaction seed words from gap #1, not official
   political keywords. The comment sections on these videos are the corpus.

2. **`crawlers/zhihu.py`** (new file, subclass `BaseCrawler`) — answer comment
   threads on "如何看待XX" questions are extremely clean sources of ironic 句式.
   API: `www.zhihu.com/api/v4/answers/<id>/comments?limit=20&offset=<n>`. Public
   for non-sensitive questions; no auth.

3. **`crawlers/weibo.py`** (new file) — trending topic comment streams via
   `m.weibo.cn/api/container/getIndex?containerid=<cid>`. Seed with meme/reaction
   topic container IDs, not official news hashtags.

### Phase 2 — Pattern rules and one-slot support

4. **`nlp/extractor.py:_build_regex`** — add one-slot branch: if `conn_b is None`
   *and* `{slot1}` appears in the template string, build `(?P<slot1>[^。！？\n]{1,20}?)`
   pattern with the suffix lookahead. Currently the `conn_b is None` branch only
   handles fixed idioms with no slots.

5. **`nlp/extractor.py:CONNECTIVE_RULES`** — add the 12 ironic/meme patterns from
   gap #2. One-slot entries use `None` for `conn_b` and include `{slot1}` in the
   template string to distinguish from fixed idioms.

### Phase 3 — Subvariant schema

6. **`alembic/versions/`** — new migration:
   - `sentence_patterns.canonical_template_id` (nullable FK → self)
   - `UniqueConstraint("pattern_id", "content")` on `pattern_examples`
   - Index on `canonical_template_id`

7. **`app/models.py`** — add `canonical_template_id` mapped column and `variants`
   back-relationship on `SentencePattern`.

8. **`nlp/run_pipeline.py:process_text`** — after inserting a new `SentencePattern`,
   check Levenshtein distance against existing templates (via
   `difflib.SequenceMatcher`). If distance ≤ 3 to an existing canonical, set
   `canonical_template_id` to that canonical's id.

### Phase 4 — DB integrity and tagger

9. **`nlp/run_pipeline.py:process_text`** — server-side `source_count` increment
   (gap #5) and `pg_insert … on_conflict_do_nothing` for `PatternExample` (gap #4).

10. **`nlp/tagger.py`** — add `借古讽今`, `反向感谢`, `梗引用`, `反问讽刺` tags;
    replace `阴阳怪气` keyword list with the in-pattern signals from gap #6.

---

## Longer-term (after Phase 1–4 are stable)

- **Semantic clustering:** encode all `raw_content` with
  `paraphrase-multilingual-MiniLM-L12-v2`, FAISS-cluster at cosine threshold 0.85,
  prompt an LLM to generate a canonical template per cluster. This discovers meme
  frames the rule list doesn't know about yet — especially newly coined ones that
  emerged after the rules were written.

- **Temporal subvariant tracking:** add `created_at` comparison to canonical
  linking — earlier template is always the canonical, later one is the drift variant.
  This lets the search surface show meme evolution chronologically.

- **APScheduler / Railway cron:** daily `crawl --keywords 社会热点 时事吐槽 网络热梗`
  to keep the corpus current with the news cycle that drives meme production.

- **Slot-filling semantic analysis:** when `slot1` is frequently filled with proper
  nouns (event names, figures, places), that pattern is likely an intertextual
  reference frame (借古讽今 type). Flag these automatically as higher-value 句式.

- **Example quality scoring:** flag examples where slot_fillings are single
  characters, stopwords, or repeat the connective — these are false-positive matches
  from the regex and should be excluded from clustering input.
