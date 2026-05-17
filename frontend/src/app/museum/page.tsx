'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getTrending, type Pattern } from '@/lib/api';

// ─── Card color themes ────────────────────────────────────────────────────────

const CARD_THEMES = [
  {
    bg: 'bg-indigo-950',
    border: 'border-indigo-800',
    text: 'text-indigo-100',
    accent: 'text-indigo-400',
    tag: 'bg-indigo-900 text-indigo-300',
    glyph: 'text-indigo-800',
  },
  {
    bg: 'bg-rose-950',
    border: 'border-rose-800',
    text: 'text-rose-100',
    accent: 'text-rose-400',
    tag: 'bg-rose-900 text-rose-300',
    glyph: 'text-rose-800',
  },
  {
    bg: 'bg-amber-950',
    border: 'border-amber-800',
    text: 'text-amber-100',
    accent: 'text-amber-400',
    tag: 'bg-amber-900 text-amber-300',
    glyph: 'text-amber-800',
  },
  {
    bg: 'bg-emerald-950',
    border: 'border-emerald-800',
    text: 'text-emerald-100',
    accent: 'text-emerald-400',
    tag: 'bg-emerald-900 text-emerald-300',
    glyph: 'text-emerald-800',
  },
  {
    bg: 'bg-violet-950',
    border: 'border-violet-800',
    text: 'text-violet-100',
    accent: 'text-violet-400',
    tag: 'bg-violet-900 text-violet-300',
    glyph: 'text-violet-800',
  },
  {
    bg: 'bg-sky-950',
    border: 'border-sky-800',
    text: 'text-sky-100',
    accent: 'text-sky-400',
    tag: 'bg-sky-900 text-sky-300',
    glyph: 'text-sky-800',
  },
  {
    bg: 'bg-zinc-900',
    border: 'border-zinc-700',
    text: 'text-zinc-100',
    accent: 'text-zinc-400',
    tag: 'bg-zinc-800 text-zinc-300',
    glyph: 'text-zinc-800',
  },
  {
    bg: 'bg-orange-950',
    border: 'border-orange-800',
    text: 'text-orange-100',
    accent: 'text-orange-400',
    tag: 'bg-orange-900 text-orange-300',
    glyph: 'text-orange-800',
  },
];

// Decorative Chinese glyphs for card backgrounds
const BG_GLYPHS = ['式', '句', '语', '言', '词', '文', '典', '梗', '评'];

// ─── Museum card ──────────────────────────────────────────────────────────────

function MuseumCard({ pattern, index }: { pattern: Pattern; index: number }) {
  const theme = CARD_THEMES[index % CARD_THEMES.length];
  const glyph = BG_GLYPHS[index % BG_GLYPHS.length];
  const firstExample = pattern.examples?.[0];

  // Render template with slot highlights
  function renderTemplate(template: string) {
    const parts = template.split(/(\{[^}]+\}|\*)/g);
    return parts.map((part, i) => {
      const isSlot = (part.startsWith('{') && part.endsWith('}')) || part === '*';
      if (isSlot) {
        const label = part === '*' ? '___' : part.slice(1, -1);
        return (
          <span key={i} className={`${theme.accent} italic font-light border-b border-current pb-0.5`}>
            {label}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  }

  return (
    <Link
      href={`/pattern/${pattern.id}`}
      className={`
        masonry-item block relative overflow-hidden rounded-2xl border ${theme.border} ${theme.bg}
        p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl group
      `}
      style={{ animationDelay: `${0.07 * index}s` }}
    >
      {/* Background decorative glyph */}
      <div
        className={`absolute -bottom-4 -right-4 text-[8rem] font-black ${theme.glyph} select-none pointer-events-none transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3`}
        style={{ fontFamily: "'Noto Serif SC', serif", lineHeight: 1 }}
      >
        {glyph}
      </div>

      {/* Content */}
      <div className="relative">
        {/* Tags */}
        {pattern.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {pattern.tags.slice(0, 2).map((tag) => (
              <span
                key={tag.id}
                className={`text-xs px-2 py-0.5 rounded-full ${theme.tag} font-medium`}
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Template — the star */}
        <p
          className={`text-xl sm:text-2xl font-bold ${theme.text} leading-relaxed mb-5`}
          style={{ fontFamily: "'Noto Serif SC', serif", letterSpacing: '0.06em' }}
        >
          {renderTemplate(pattern.template)}
        </p>

        {/* Example quote */}
        {firstExample && (
          <blockquote className={`text-sm ${theme.accent} opacity-80 leading-relaxed mb-4 pl-3 border-l border-current`}>
            {firstExample.text}
          </blockquote>
        )}

        {/* Stats footer */}
        <div className={`flex items-center justify-between text-xs ${theme.accent} opacity-60 mt-2`}>
          <span>{pattern.example_count.toLocaleString()} 例句</span>
          <span className="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
            {pattern.usage_count.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Hover shimmer */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-300 pointer-events-none"
        style={{ background: 'linear-gradient(135deg, white, transparent)' }} />
    </Link>
  );
}

function MuseumCardSkeleton() {
  return (
    <div className="masonry-item rounded-2xl overflow-hidden">
      <div className="skeleton h-52 rounded-2xl" />
    </div>
  );
}

// ─── Mock museum data ─────────────────────────────────────────────────────────

const MOCK_MUSEUM_PATTERNS: Pattern[] = [
  {
    id: 1, template: '只有{A}才能{B}', example_count: 1842, usage_count: 9201, created_at: '2024-01-01',
    tags: [{ id: 1, name: '强调', slug: '强调' }],
    examples: [{ id: 1, pattern_id: 1, text: '只有努力学习才能取得好成绩' }],
  },
  {
    id: 4, template: '我以为{A}，没想到{B}', example_count: 3201, usage_count: 15820, created_at: '2024-01-04',
    tags: [{ id: 7, name: '反转', slug: '反转' }],
    examples: [{ id: 4, pattern_id: 4, text: '我以为他在摸鱼，没想到他已经做完了三个项目' }],
  },
  {
    id: 3, template: '{A}的尽头是{B}', example_count: 892, usage_count: 4320, created_at: '2024-01-03',
    tags: [{ id: 5, name: '哲学', slug: '哲学' }],
    examples: [{ id: 3, pattern_id: 3, text: '卷的尽头是躺平' }],
  },
  {
    id: 12, template: '说好的{A}呢', example_count: 3421, usage_count: 16700, created_at: '2024-01-12',
    tags: [{ id: 14, name: '神转折', slug: '神转折' }],
    examples: [{ id: 12, pattern_id: 12, text: '说好的双休呢' }],
  },
  {
    id: 5, template: '{A}是{B}的最高形式', example_count: 456, usage_count: 2103, created_at: '2024-01-05',
    tags: [{ id: 9, name: '升华', slug: '升华' }],
    examples: [{ id: 5, pattern_id: 5, text: '摸鱼是对资本主义的最高形式抵抗' }],
  },
  {
    id: 6, template: '都{A}了，还在意{B}', example_count: 1203, usage_count: 6541, created_at: '2024-01-06',
    tags: [{ id: 10, name: '调侃', slug: '调侃' }],
    examples: [{ id: 6, pattern_id: 6, text: '都三十岁了，还在意什么面子' }],
  },
  {
    id: 2, template: '不是{A}，而是{B}', example_count: 2341, usage_count: 11205, created_at: '2024-01-02',
    tags: [{ id: 3, name: '对比', slug: '对比' }],
    examples: [{ id: 2, pattern_id: 2, text: '不是我不努力，而是对手太强了' }],
  },
  {
    id: 8, template: '如果{A}，那{B}', example_count: 2890, usage_count: 13200, created_at: '2024-01-08',
    tags: [{ id: 11, name: '条件句', slug: '条件句' }],
    examples: [{ id: 8, pattern_id: 8, text: '如果生活欺骗了你，那你就欺骗生活' }],
  },
  {
    id: 9, template: '凭什么{A}就要{B}', example_count: 1567, usage_count: 7823, created_at: '2024-01-09',
    tags: [{ id: 13, name: '反问', slug: '反问' }],
    examples: [{ id: 9, pattern_id: 9, text: '凭什么年轻就要加班' }],
  },
  {
    id: 10, template: '与其{A}不如{B}', example_count: 2100, usage_count: 9870, created_at: '2024-01-10',
    tags: [{ id: 3, name: '对比', slug: '对比' }],
    examples: [{ id: 10, pattern_id: 10, text: '与其担心未来，不如专注当下' }],
  },
  {
    id: 7, template: '{A}，这才是{B}', example_count: 789, usage_count: 3456, created_at: '2024-01-07',
    tags: [{ id: 9, name: '升华', slug: '升华' }],
    examples: [{ id: 7, pattern_id: 7, text: '躺平，这才是真正的自由' }],
  },
  {
    id: 11, template: '{A}到底是不是{B}', example_count: 934, usage_count: 4102, created_at: '2024-01-11',
    tags: [{ id: 15, name: '整活', slug: '整活' }],
    examples: [{ id: 11, pattern_id: 11, text: '老板到底是不是人' }],
  },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function MuseumPage() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [range, setRange] = useState('week');

  useEffect(() => {
    setIsLoading(true);
    getTrending(range)
      .then((data) => setPatterns(data.items))
      .catch(() => setPatterns(MOCK_MUSEUM_PATTERNS))
      .finally(() => setIsLoading(false));
  }, [range]);

  return (
    <div>
      {/* Museum hero */}
      <div className="relative overflow-hidden bg-zinc-950 text-white">
        {/* Decorative layer */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-full h-full opacity-20"
            style={{
              backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.04) 39px, rgba(255,255,255,0.04) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.04) 39px, rgba(255,255,255,0.04) 40px)',
            }}
          />
          <div className="absolute -top-20 left-1/3 w-96 h-96 rounded-full blur-3xl opacity-20"
            style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />
          <div className="absolute bottom-0 right-1/4 w-64 h-64 rounded-full blur-3xl opacity-15"
            style={{ background: 'radial-gradient(circle, #f7523a, transparent)' }} />
        </div>

        {/* Large decorative Chinese chars */}
        <div className="absolute top-0 right-0 leading-none select-none pointer-events-none"
          style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 'clamp(120px, 20vw, 240px)', color: 'rgba(255,255,255,0.03)', lineHeight: 0.9 }}>
          神评
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-16 sm:py-24">
          <div className="max-w-2xl animate-fade-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-px bg-indigo-500" />
              <span className="text-xs text-indigo-400 uppercase tracking-widest font-medium">Museum</span>
            </div>
            <h1 className="text-4xl sm:text-6xl font-black mb-4 leading-tight"
              style={{ fontFamily: "'Noto Serif SC', serif", letterSpacing: '0.04em' }}>
              神评<span className="text-indigo-400">博物馆</span>
            </h1>
            <p className="text-zinc-400 text-lg leading-relaxed">
              收录那些一换槽位就能把人带回原始场面的网络句式。
              每一句都是被反复借用的记忆框架。
            </p>

            {/* Range selector */}
            <div className="flex items-center gap-2 mt-8">
              <span className="text-xs text-zinc-500 uppercase tracking-wider">展出范围</span>
              {[
                { value: 'day', label: '今日' },
                { value: 'week', label: '本周' },
                { value: 'month', label: '本月' },
                { value: 'all', label: '全部' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setRange(opt.value)}
                  className={`text-sm px-4 py-1.5 rounded-lg border transition-all ${
                    range === opt.value
                      ? 'border-indigo-500 bg-indigo-500/20 text-indigo-300'
                      : 'border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Masonry grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        {isLoading ? (
          <div className="masonry-grid">
            {Array.from({ length: 9 }).map((_, i) => (
              <MuseumCardSkeleton key={i} />
            ))}
          </div>
        ) : patterns.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-5xl mb-4 opacity-30" style={{ fontFamily: "'Noto Serif SC', serif" }}>空</p>
            <p className="text-[var(--color-text-muted)]">暂无展出句式</p>
          </div>
        ) : (
          <div className="masonry-grid">
            {patterns.map((pattern, i) => (
              <div key={pattern.id} className="masonry-item animate-fade-up" style={{ animationDelay: `${0.06 * i}s` }}>
                <MuseumCard pattern={pattern} index={i} />
              </div>
            ))}
          </div>
        )}

        {/* Bottom CTA */}
        {!isLoading && patterns.length > 0 && (
          <div className="mt-16 text-center animate-fade-up" style={{ animationDelay: '0.5s' }}>
            <p className="text-[var(--color-text-muted)] text-sm mb-4">
              探索更多 JuShi，查看它们如何在不同场景中被借用
            </p>
            <Link
              href="/browse"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-500 text-white font-semibold hover:bg-indigo-600 transition-colors"
            >
              浏览全部 JuShi
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
