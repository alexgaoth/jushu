'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { searchPatterns, getTrending, type Pattern, type SearchResult, type TrendingResult } from '@/lib/api';
import { PatternCard, PatternCardSkeleton } from '@/components/PatternCard';
import { SearchBar } from '@/components/SearchBar';

// ─── Decorative hero background ──────────────────────────────────────────────

function HeroBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Gradient blob 1 */}
      <div
        className="absolute -top-20 left-1/4 w-96 h-96 rounded-full opacity-20 blur-3xl"
        style={{ background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)' }}
      />
      {/* Gradient blob 2 */}
      <div
        className="absolute top-10 right-1/4 w-64 h-64 rounded-full opacity-10 blur-3xl"
        style={{ background: 'radial-gradient(circle, #f7523a 0%, transparent 70%)' }}
      />
      {/* Decorative Chinese characters */}
      <div className="absolute top-8 left-8 text-8xl font-bold opacity-[0.03] select-none"
        style={{ fontFamily: "'Noto Serif SC', serif" }}>
        式
      </div>
      <div className="absolute bottom-8 right-8 text-8xl font-bold opacity-[0.03] select-none rotate-12"
        style={{ fontFamily: "'Noto Serif SC', serif" }}>
        句
      </div>
    </div>
  );
}

// ─── Trending / empty state ───────────────────────────────────────────────────

function TrendingSection({ patterns }: { patterns: Pattern[] }) {
  return (
    <div className="animate-fade-up" style={{ animationDelay: '0.2s' }}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-5 bg-indigo-500 rounded-full" />
        <h2 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">
          本周热门句式
        </h2>
        <div className="flex-1 h-px bg-[var(--color-border)]" />
        <span className="text-xs text-indigo-400 font-mono">热</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {patterns.map((pattern, i) => (
          <PatternCard
            key={pattern.id}
            pattern={pattern}
            className="animate-fade-up"
            style={{ animationDelay: `${0.1 * (i + 1)}s` }}
          />
        ))}
      </div>
    </div>
  );
}

function ExampleQueries() {
  const examples = [
    '只有*才*',
    '不是*而是*',
    '我选择*',
    '什么是*',
    '*的*是*',
    '如果*那*',
  ];

  return (
    <div className="flex flex-wrap gap-2 justify-center mt-4">
      <span className="text-xs text-[var(--color-text-muted)] self-center">试试：</span>
      {examples.map((ex) => (
        <a
          key={ex}
          href={`/?q=${encodeURIComponent(ex)}`}
          className="text-xs px-3 py-1.5 rounded-full border border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-500 transition-all duration-150 font-mono bg-[var(--color-surface)]"
        >
          {ex}
        </a>
      ))}
    </div>
  );
}

// ─── Search results ───────────────────────────────────────────────────────────

function SearchResults({
  results,
  isLoading,
  query,
  page,
  onPageChange,
}: {
  results: SearchResult | null;
  isLoading: boolean;
  query: string;
  page: number;
  onPageChange: (p: number) => void;
}) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <PatternCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!results || results.items.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-up">
        <div className="text-5xl mb-4 opacity-30" style={{ fontFamily: "'Noto Serif SC', serif" }}>
          ？
        </div>
        <p className="text-[var(--color-text-muted)] text-lg mb-2">
          没有找到「{query}」相关的句式
        </p>
        <p className="text-sm text-[var(--color-text-muted)]/70">
          试试使用 <code className="bg-[var(--color-border)] px-1.5 py-0.5 rounded font-mono text-xs">*</code> 通配符，例如「只有*才*」
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Result count */}
      <div className="flex items-center justify-between mb-5">
        <p className="text-sm text-[var(--color-text-muted)]">
          找到 <span className="text-[var(--color-text)] font-semibold">{results.total.toLocaleString()}</span> 个句式
        </p>
        <p className="text-xs text-[var(--color-text-muted)] font-mono">
          第 {page} / {results.pages} 页
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {results.items.map((pattern, i) => (
          <PatternCard
            key={pattern.id}
            pattern={pattern}
            className="animate-fade-up"
            style={{ animationDelay: `${0.05 * i}s` }}
          />
        ))}
      </div>

      {/* Pagination */}
      {results.pages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-4 py-2 rounded-xl text-sm border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            上一页
          </button>
          {Array.from({ length: Math.min(5, results.pages) }).map((_, i) => {
            const p = Math.max(1, Math.min(results.pages - 4, page - 2)) + i;
            return (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={`px-4 py-2 rounded-xl text-sm border transition-all ${
                  p === page
                    ? 'border-indigo-500 bg-indigo-500 text-white'
                    : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400'
                }`}
              >
                {p}
              </button>
            );
          })}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= results.pages}
            className="px-4 py-2 rounded-xl text-sm border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [trendingData, setTrendingData] = useState<TrendingResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingTrending, setIsLoadingTrending] = useState(true);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Load trending on mount
  useEffect(() => {
    setIsLoadingTrending(true);
    getTrending('week')
      .then((data) => setTrendingData(data))
      .catch(() => {
        // Show mock data if API is unavailable
        setTrendingData({
          range: 'week',
          items: MOCK_TRENDING,
        });
      })
      .finally(() => setIsLoadingTrending(false));
  }, []);

  // Check URL params on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const q = params.get('q');
      if (q) {
        setQuery(q);
        doSearch(q, 1);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const doSearch = useCallback(async (q: string, p: number = 1) => {
    if (!q.trim()) {
      setSearchResults(null);
      setError(null);
      return;
    }

    // Abort previous request
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setIsSearching(true);
    setError(null);

    try {
      const results = await searchPatterns(q, p, 18);
      setSearchResults(results);
      setPage(p);

      // Update URL
      const url = new URL(window.location.href);
      url.searchParams.set('q', q);
      window.history.replaceState({}, '', url.toString());
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        // Fall back to mock for demo
        setSearchResults({
          items: MOCK_TRENDING.filter(p =>
            p.template.includes(q.replace(/\*/g, '')) || q === ''
          ).slice(0, 6),
          total: 6,
          page: p,
          size: 18,
          pages: 1,
          query: q,
        });
      }
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSearch = useCallback((q: string) => {
    setPage(1);
    doSearch(q, 1);
  }, [doSearch]);

  const handlePageChange = useCallback((p: number) => {
    doSearch(query, p);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [query, doSearch]);

  const hasQuery = query.trim().length > 0;
  const showResults = hasQuery;

  return (
    <div className="relative">
      {/* Hero section */}
      <section className="relative overflow-hidden py-16 sm:py-24">
        <HeroBackground />

        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
          {/* Headline */}
          <div className="mb-8 animate-fade-up">
            <h1 className="text-3xl sm:text-5xl font-bold mb-3 text-[var(--color-text)]"
              style={{ fontFamily: "'Noto Serif SC', serif", letterSpacing: '0.05em' }}>
              句式搜索引擎
            </h1>
            <p className="text-[var(--color-text-muted)] text-base sm:text-lg">
              收录中文网络<span className="text-indigo-500 font-medium">固定句式</span>，探索语言的模式与创意
            </p>
          </div>

          {/* Search bar */}
          <div className="animate-fade-up" style={{ animationDelay: '0.1s' }}>
            <SearchBar
              value={query}
              onChange={setQuery}
              onSearch={handleSearch}
              autoFocus
              size="lg"
              className="max-w-2xl mx-auto"
            />
            <ExampleQueries />
          </div>

          {/* Stats bar */}
          <div className="mt-8 flex items-center justify-center gap-8 animate-fade-up" style={{ animationDelay: '0.3s' }}>
            {[
              { label: '句式收录', value: '10,000+' },
              { label: '例句样本', value: '50万+' },
              { label: '标签分类', value: '200+' },
            ].map(({ label, value }) => (
              <div key={label} className="text-center">
                <div className="text-xl font-bold text-indigo-500" style={{ fontFamily: "'Noto Serif SC', serif" }}>
                  {value}
                </div>
                <div className="text-xs text-[var(--color-text-muted)] mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr className="ink-rule mx-4 sm:mx-6" />

      {/* Content section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        {showResults ? (
          <SearchResults
            results={searchResults}
            isLoading={isSearching}
            query={query}
            page={page}
            onPageChange={handlePageChange}
          />
        ) : isLoadingTrending ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <PatternCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <TrendingSection patterns={trendingData?.items || MOCK_TRENDING} />
        )}
      </section>
    </div>
  );
}

// ─── Mock data for offline/demo ───────────────────────────────────────────────

const MOCK_TRENDING: Pattern[] = [
  {
    id: 1,
    template: '只有{A}才能{B}',
    example_count: 1842,
    usage_count: 9201,
    created_at: '2024-01-01',
    tags: [{ id: 1, name: '强调', slug: '强调' }, { id: 2, name: '逻辑', slug: '逻辑' }],
    examples: [{ id: 1, pattern_id: 1, text: '只有努力学习才能取得好成绩' }],
  },
  {
    id: 2,
    template: '不是{A}，而是{B}',
    example_count: 2341,
    usage_count: 11205,
    created_at: '2024-01-02',
    tags: [{ id: 3, name: '对比', slug: '对比' }, { id: 4, name: '纠正', slug: '纠正' }],
    examples: [{ id: 2, pattern_id: 2, text: '不是我不努力，而是对手太强了' }],
  },
  {
    id: 3,
    template: '{A}的尽头是{B}',
    example_count: 892,
    usage_count: 4320,
    created_at: '2024-01-03',
    tags: [{ id: 5, name: '哲学', slug: '哲学' }, { id: 6, name: '感悟', slug: '感悟' }],
    examples: [{ id: 3, pattern_id: 3, text: '卷的尽头是躺平' }],
  },
  {
    id: 4,
    template: '我以为{A}，没想到{B}',
    example_count: 3201,
    usage_count: 15820,
    created_at: '2024-01-04',
    tags: [{ id: 7, name: '反转', slug: '反转' }, { id: 8, name: '吐槽', slug: '吐槽' }],
    examples: [{ id: 4, pattern_id: 4, text: '我以为他在摸鱼，没想到他已经做完了三个项目' }],
  },
  {
    id: 5,
    template: '{A}是{B}的最高形式',
    example_count: 456,
    usage_count: 2103,
    created_at: '2024-01-05',
    tags: [{ id: 9, name: '升华', slug: '升华' }, { id: 1, name: '强调', slug: '强调' }],
    examples: [{ id: 5, pattern_id: 5, text: '摸鱼是对资本主义的最高形式抵抗' }],
  },
  {
    id: 6,
    template: '都{A}了，还在意{B}',
    example_count: 1203,
    usage_count: 6541,
    created_at: '2024-01-06',
    tags: [{ id: 10, name: '调侃', slug: '调侃' }, { id: 8, name: '吐槽', slug: '吐槽' }],
    examples: [{ id: 6, pattern_id: 6, text: '都三十岁了，还在意什么面子' }],
  },
];
