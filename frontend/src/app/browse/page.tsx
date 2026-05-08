'use client';

import { useState, useEffect, useCallback } from 'react';
import { browsePatterns, getTags, type Pattern, type Tag } from '@/lib/api';
import { PatternCard, PatternCardSkeleton } from '@/components/PatternCard';
import { TagChip } from '@/components/TagChip';

// ─── Mock data ────────────────────────────────────────────────────────────────

const MOCK_TAGS: Tag[] = [
  { id: 1, name: '强调', slug: '强调', count: 234 },
  { id: 2, name: '逻辑', slug: '逻辑', count: 189 },
  { id: 3, name: '对比', slug: '对比', count: 312 },
  { id: 4, name: '纠正', slug: '纠正', count: 97 },
  { id: 5, name: '哲学', slug: '哲学', count: 156 },
  { id: 6, name: '感悟', slug: '感悟', count: 203 },
  { id: 7, name: '反转', slug: '反转', count: 421 },
  { id: 8, name: '吐槽', slug: '吐槽', count: 567 },
  { id: 9, name: '升华', slug: '升华', count: 88 },
  { id: 10, name: '调侃', slug: '调侃', count: 334 },
  { id: 11, name: '条件句', slug: '条件句', count: 278 },
  { id: 12, name: '排比', slug: '排比', count: 145 },
  { id: 13, name: '反问', slug: '反问', count: 219 },
  { id: 14, name: '神转折', slug: '神转折', count: 389 },
  { id: 15, name: '整活', slug: '整活', count: 612 },
];

const MOCK_PATTERNS: Pattern[] = [
  {
    id: 1, template: '只有{A}才能{B}', example_count: 1842, usage_count: 9201, created_at: '2024-01-01',
    tags: [{ id: 1, name: '强调', slug: '强调' }, { id: 2, name: '逻辑', slug: '逻辑' }],
    examples: [{ id: 1, pattern_id: 1, text: '只有努力学习才能取得好成绩' }],
  },
  {
    id: 2, template: '不是{A}，而是{B}', example_count: 2341, usage_count: 11205, created_at: '2024-01-02',
    tags: [{ id: 3, name: '对比', slug: '对比' }, { id: 4, name: '纠正', slug: '纠正' }],
    examples: [{ id: 2, pattern_id: 2, text: '不是我不努力，而是对手太强了' }],
  },
  {
    id: 3, template: '{A}的尽头是{B}', example_count: 892, usage_count: 4320, created_at: '2024-01-03',
    tags: [{ id: 5, name: '哲学', slug: '哲学' }, { id: 6, name: '感悟', slug: '感悟' }],
    examples: [{ id: 3, pattern_id: 3, text: '卷的尽头是躺平' }],
  },
  {
    id: 4, template: '我以为{A}，没想到{B}', example_count: 3201, usage_count: 15820, created_at: '2024-01-04',
    tags: [{ id: 7, name: '反转', slug: '反转' }, { id: 8, name: '吐槽', slug: '吐槽' }],
    examples: [{ id: 4, pattern_id: 4, text: '我以为他在摸鱼，没想到他已经做完了三个项目' }],
  },
  {
    id: 5, template: '{A}是{B}的最高形式', example_count: 456, usage_count: 2103, created_at: '2024-01-05',
    tags: [{ id: 9, name: '升华', slug: '升华' }, { id: 1, name: '强调', slug: '强调' }],
    examples: [{ id: 5, pattern_id: 5, text: '摸鱼是对资本主义的最高形式抵抗' }],
  },
  {
    id: 6, template: '都{A}了，还在意{B}', example_count: 1203, usage_count: 6541, created_at: '2024-01-06',
    tags: [{ id: 10, name: '调侃', slug: '调侃' }, { id: 8, name: '吐槽', slug: '吐槽' }],
    examples: [{ id: 6, pattern_id: 6, text: '都三十岁了，还在意什么面子' }],
  },
  {
    id: 7, template: '{A}，这才是{B}', example_count: 789, usage_count: 3456, created_at: '2024-01-07',
    tags: [{ id: 9, name: '升华', slug: '升华' }, { id: 6, name: '感悟', slug: '感悟' }],
    examples: [{ id: 7, pattern_id: 7, text: '躺平，这才是真正的自由' }],
  },
  {
    id: 8, template: '如果{A}，那{B}', example_count: 2890, usage_count: 13200, created_at: '2024-01-08',
    tags: [{ id: 11, name: '条件句', slug: '条件句' }],
    examples: [{ id: 8, pattern_id: 8, text: '如果生活欺骗了你，那你就欺骗生活' }],
  },
  {
    id: 9, template: '凭什么{A}就要{B}', example_count: 1567, usage_count: 7823, created_at: '2024-01-09',
    tags: [{ id: 13, name: '反问', slug: '反问' }, { id: 8, name: '吐槽', slug: '吐槽' }],
    examples: [{ id: 9, pattern_id: 9, text: '凭什么年轻就要加班' }],
  },
  {
    id: 10, template: '与其{A}不如{B}', example_count: 2100, usage_count: 9870, created_at: '2024-01-10',
    tags: [{ id: 3, name: '对比', slug: '对比' }, { id: 6, name: '感悟', slug: '感悟' }],
    examples: [{ id: 10, pattern_id: 10, text: '与其担心未来，不如专注当下' }],
  },
  {
    id: 11, template: '{A}到底是不是{B}', example_count: 934, usage_count: 4102, created_at: '2024-01-11',
    tags: [{ id: 13, name: '反问', slug: '反问' }, { id: 15, name: '整活', slug: '整活' }],
    examples: [{ id: 11, pattern_id: 11, text: '老板到底是不是人' }],
  },
  {
    id: 12, template: '说好的{A}呢', example_count: 3421, usage_count: 16700, created_at: '2024-01-12',
    tags: [{ id: 14, name: '神转折', slug: '神转折' }, { id: 8, name: '吐槽', slug: '吐槽' }],
    examples: [{ id: 12, pattern_id: 12, text: '说好的双休呢' }],
  },
];

// ─── Sort options ─────────────────────────────────────────────────────────────

const SORT_OPTIONS = [
  { value: 'usage', label: '热度' },
  { value: 'newest', label: '最新' },
  { value: 'examples', label: '例句数' },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function BrowsePage() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [tags, setTagsList] = useState<Tag[]>([]);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [sort, setSort] = useState('usage');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [tagsLoading, setTagsLoading] = useState(true);

  // Load tags
  useEffect(() => {
    getTags()
      .then(setTagsList)
      .catch(() => setTagsList(MOCK_TAGS))
      .finally(() => setTagsLoading(false));
  }, []);

  // Load patterns
  const loadPatterns = useCallback(async (p: number, tag: string | null, s: string) => {
    setIsLoading(true);
    try {
      const data = await browsePatterns(p, 24, tag || undefined, s);
      setPatterns(data.items);
      setTotal(data.total);
      setTotalPages(data.pages);
    } catch {
      // Filter mock data by tag
      let filtered = MOCK_PATTERNS;
      if (tag) {
        filtered = MOCK_PATTERNS.filter(pt => pt.tags.some(t => t.slug === tag));
      }
      if (s === 'newest') {
        filtered = [...filtered].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      } else if (s === 'examples') {
        filtered = [...filtered].sort((a, b) => b.example_count - a.example_count);
      } else {
        filtered = [...filtered].sort((a, b) => b.usage_count - a.usage_count);
      }
      setPatterns(filtered);
      setTotal(filtered.length);
      setTotalPages(1);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPatterns(page, selectedTag, sort);
  }, [page, selectedTag, sort, loadPatterns]);

  const handleTagClick = (tag: Tag) => {
    const newTag = selectedTag === tag.slug ? null : tag.slug;
    setSelectedTag(newTag);
    setPage(1);
  };

  const handleSortChange = (s: string) => {
    setSort(s);
    setPage(1);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
      {/* Page header */}
      <div className="mb-10 animate-fade-up">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-1 h-7 bg-indigo-500 rounded-full" />
          <h1 className="text-2xl sm:text-3xl font-bold text-[var(--color-text)]"
            style={{ fontFamily: "'Noto Serif SC', serif" }}>
            发现句式
          </h1>
        </div>
        <p className="text-[var(--color-text-muted)] ml-4 pl-3">
          浏览收录的 <span className="text-indigo-500 font-medium">{total.toLocaleString()}</span> 个中文网络固定句式
        </p>
      </div>

      {/* Filter bar */}
      <div className="mb-8 animate-fade-up" style={{ animationDelay: '0.1s' }}>
        <div className="flex flex-col gap-4">
          {/* Sort + stats row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">排序</span>
              <div className="flex gap-1">
                {SORT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleSortChange(opt.value)}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                      sort === opt.value
                        ? 'border-indigo-500 bg-indigo-500 text-white'
                        : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {selectedTag && (
              <button
                onClick={() => { setSelectedTag(null); setPage(1); }}
                className="text-xs text-[var(--color-text-muted)] hover:text-indigo-500 flex items-center gap-1 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
                清除筛选
              </button>
            )}
          </div>

          {/* Tag filter */}
          <div className="flex flex-wrap gap-2">
            {tagsLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="skeleton h-7 rounded-full" style={{ width: `${60 + i * 8}px` }} />
              ))
            ) : (
              tags.map((tag) => (
                <TagChip
                  key={tag.id}
                  tag={tag}
                  size="sm"
                  onClick={handleTagClick}
                  active={selectedTag === tag.slug}
                />
              ))
            )}
          </div>
        </div>
      </div>

      <hr className="ink-rule mb-8" />

      {/* Pattern grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <PatternCardSkeleton key={i} />
          ))}
        </div>
      ) : patterns.length === 0 ? (
        <div className="text-center py-20 animate-fade-up">
          <div className="text-5xl mb-4 opacity-30" style={{ fontFamily: "'Noto Serif SC', serif" }}>空</div>
          <p className="text-[var(--color-text-muted)]">该标签下暂无句式</p>
          <button
            onClick={() => { setSelectedTag(null); setPage(1); }}
            className="mt-4 text-sm text-indigo-500 hover:underline"
          >
            查看全部句式
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-10">
            {patterns.map((pattern, i) => (
              <PatternCard
                key={pattern.id}
                pattern={pattern}
                className="animate-fade-up"
                style={{ animationDelay: `${0.04 * (i % 12)}s` }}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-4 py-2 rounded-xl text-sm border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                上一页
              </button>
              {Array.from({ length: Math.min(7, totalPages) }).map((_, i) => {
                const p = Math.max(1, Math.min(totalPages - 6, page - 3)) + i;
                if (p > totalPages) return null;
                return (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
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
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-4 py-2 rounded-xl text-sm border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
