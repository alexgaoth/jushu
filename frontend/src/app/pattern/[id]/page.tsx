'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  getPattern, getExamples, generateFromPattern,
  parseSlots, fillTemplate,
  type Pattern, type Example,
} from '@/lib/api';
import { TagList } from '@/components/TagChip';
import { MOCK_PATTERN_DATA } from './mockData';

// ─── Template display with slot highlighting ──────────────────────────────────

function TemplateDisplay({ template, values }: { template: string; values: Record<string, string> }) {
  const parts = template.split(/(\{[^}]+\}|\*)/g);

  return (
    <span className="pattern-template">
      {parts.map((part, i) => {
        const isSlot = (part.startsWith('{') && part.endsWith('}')) || part === '*';
        if (isSlot) {
          const name = part === '*' ? '' : part.slice(1, -1);
          const filled = name && values[name];
          return (
            <span
              key={i}
              className={`inline-block px-1.5 mx-0.5 rounded transition-all duration-200 border-b-2 ${
                filled
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 not-italic'
                  : 'border-indigo-300 bg-indigo-50/50 text-indigo-400 dark:bg-indigo-950/30 italic'
              }`}
            >
              {filled ? values[name] : (name || '___')}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}

// ─── Fill & Generate widget ───────────────────────────────────────────────────

function GenerateWidget({ pattern }: { pattern: Pattern }) {
  const slots = parseSlots(pattern.template);
  const [values, setValues] = useState<Record<string, string>>({});
  const [generatedText, setGeneratedText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  // Real-time preview
  const preview = fillTemplate(pattern.template, values);
  const hasAllSlots = slots.every((s) => values[s.name]?.trim());

  const handleGenerate = async () => {
    if (!hasAllSlots) return;
    setIsGenerating(true);
    setError('');
    try {
      const result = await generateFromPattern(pattern.id, values);
      setGeneratedText(result.text);
    } catch {
      // Fallback: just use the filled template
      setGeneratedText(preview);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleReset = () => {
    setValues({});
    setGeneratedText('');
    setError('');
  };

  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-card overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse-slow" />
          <h2 className="font-semibold text-[var(--color-text)] text-sm">填空生成</h2>
        </div>
        <button
          onClick={handleReset}
          className="text-xs text-[var(--color-text-muted)] hover:text-indigo-500 transition-colors"
        >
          重置
        </button>
      </div>

      <div className="p-6">
        {slots.length === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
            此句式无需填空，可直接复制使用
          </p>
        ) : (
          <>
            {/* Slot inputs */}
            <div className="space-y-4 mb-6">
              {slots.map((slot) => (
                <div key={slot.name}>
                  <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1.5 uppercase tracking-wider">
                    {slot.name}
                  </label>
                  <input
                    type="text"
                    value={values[slot.name] || ''}
                    onChange={(e) =>
                      setValues((prev) => ({ ...prev, [slot.name]: e.target.value }))
                    }
                    placeholder={`请填写「${slot.name}」`}
                    className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20 transition-all text-sm"
                    style={{ fontFamily: "'Noto Serif SC', serif" }}
                  />
                </div>
              ))}
            </div>

            {/* Live preview */}
            <div className="mb-6 p-4 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)] mb-2 uppercase tracking-wider">预览</p>
              <p className="text-lg leading-relaxed text-[var(--color-text)]">
                <TemplateDisplay template={pattern.template} values={values} />
              </p>
            </div>
          </>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          {slots.length > 0 && (
            <button
              onClick={handleGenerate}
              disabled={!hasAllSlots || isGenerating}
              className="flex-1 py-2.5 px-4 rounded-xl bg-indigo-500 text-white font-semibold text-sm hover:bg-indigo-600 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  生成中…
                </>
              ) : '生成'}
            </button>
          )}
          <button
            onClick={() => handleCopy(generatedText || (slots.length === 0 ? pattern.template : preview))}
            className="flex items-center gap-2 py-2.5 px-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400 text-sm font-medium transition-all"
          >
            {copied ? (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-emerald-500">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
                已复制
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                  <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                  <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
                </svg>
                复制
              </>
            )}
          </button>
        </div>

        {/* Generated result */}
        {generatedText && generatedText !== preview && (
          <div className="mt-4 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800">
            <p className="text-xs text-indigo-500 mb-1.5 font-medium">生成结果</p>
            <p className="text-base text-[var(--color-text)] leading-relaxed"
              style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {generatedText}
            </p>
          </div>
        )}

        {error && (
          <p className="mt-3 text-xs text-red-500">{error}</p>
        )}
      </div>
    </div>
  );
}

// ─── Examples list ────────────────────────────────────────────────────────────

function ExamplesList({ patternId }: { patternId: number }) {
  const [examples, setExamples] = useState<Example[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState('likes');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    getExamples(patternId, page, sort)
      .then((data) => {
        setExamples(data.items);
        setTotal(data.total);
      })
      .catch(() => {
        setExamples(MOCK_EXAMPLES);
        setTotal(MOCK_EXAMPLES.length);
      })
      .finally(() => setIsLoading(false));
  }, [patternId, page, sort]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[var(--color-text)]">
          例句
          {total > 0 && (
            <span className="ml-2 text-sm text-[var(--color-text-muted)] font-normal">
              {total.toLocaleString()} 条
            </span>
          )}
        </h3>
        <div className="flex gap-1">
          {['likes', 'newest'].map((s) => (
            <button
              key={s}
              onClick={() => { setSort(s); setPage(1); }}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                sort === s
                  ? 'border-indigo-500 bg-indigo-500 text-white'
                  : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400'
              }`}
            >
              {s === 'likes' ? '最多点赞' : '最新'}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton h-14 rounded-xl" />
          ))}
        </div>
      ) : examples.length === 0 ? (
        <div className="text-center py-10 text-[var(--color-text-muted)]">
          <p>暂无例句</p>
        </div>
      ) : (
        <div className="space-y-3">
          {examples.map((ex, i) => (
            <div
              key={ex.id}
              className="p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-indigo-200 transition-colors animate-fade-up"
              style={{ animationDelay: `${0.05 * i}s` }}
            >
              <p className="text-[var(--color-text)] leading-relaxed"
                style={{ fontFamily: "'Noto Serif SC', serif" }}>
                {ex.text}
              </p>
              <div className="flex items-center justify-between mt-2">
                {ex.source && (
                  <span className="text-xs text-[var(--color-text-muted)]">来源：{ex.source}</span>
                )}
                {ex.likes !== undefined && (
                  <span className="ml-auto flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
                      <path d="M7 10v12M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
                    </svg>
                    {ex.likes.toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > 10 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-4 py-2 rounded-xl text-sm border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:border-indigo-400 hover:text-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            上一页
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={examples.length < 10}
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

export default function PatternDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [pattern, setPattern] = useState<Pattern | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    getPattern(id)
      .then(setPattern)
      .catch(() => {
        // Use mock data for demo
        const mock = MOCK_PATTERN_DATA[id] || MOCK_PATTERN_DATA[1];
        setPattern(mock);
      })
      .finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
        <div className="skeleton h-8 w-32 rounded-lg mb-8" />
        <div className="skeleton h-12 w-3/4 rounded-xl mb-4" />
        <div className="skeleton h-6 w-1/2 rounded mb-8" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="skeleton h-64 rounded-2xl" />
          <div className="skeleton h-64 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !pattern) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-24 text-center">
        <p className="text-5xl mb-4" style={{ fontFamily: "'Noto Serif SC', serif" }}>404</p>
        <p className="text-[var(--color-text-muted)] mb-6">找不到这个句式</p>
        <Link href="/" className="text-indigo-500 hover:underline">回到搜索</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-8 animate-fade-up">
        <Link href="/" className="hover:text-indigo-400 transition-colors">句式</Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">句式详情</span>
      </nav>

      {/* Pattern hero */}
      <div className="mb-10 animate-fade-up" style={{ animationDelay: '0.05s' }}>
        <div className="relative p-8 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-card overflow-hidden">
          {/* Decorative bg */}
          <div className="absolute top-0 right-0 w-48 h-48 opacity-5" style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />

          <div className="relative">
            <p className="text-2xl sm:text-3xl font-bold text-[var(--color-text)] leading-relaxed mb-4"
              style={{ fontFamily: "'Noto Serif SC', serif", letterSpacing: '0.08em' }}>
              {pattern.template}
            </p>

            {pattern.description && (
              <p className="text-[var(--color-text-muted)] text-sm mb-4 leading-relaxed">
                {pattern.description}
              </p>
            )}

            <div className="flex flex-wrap items-center gap-4">
              <TagList tags={pattern.tags} size="md" />
              <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)] ml-auto">
                <span className="flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  {pattern.example_count.toLocaleString()} 例句
                </span>
                <span className="flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                  {pattern.usage_count.toLocaleString()} 次使用
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 mb-12">
        {/* Generate widget - wider */}
        <div className="lg:col-span-2 animate-fade-up" style={{ animationDelay: '0.1s' }}>
          <GenerateWidget pattern={pattern} />
        </div>

        {/* Info sidebar */}
        <div className="lg:col-span-3 animate-fade-up" style={{ animationDelay: '0.15s' }}>
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-card p-6">
            <h3 className="font-semibold text-[var(--color-text)] mb-4 text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
              句式解析
            </h3>

            {/* Template breakdown */}
            <div className="mb-6 p-4 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-muted)] mb-2">句式模板</p>
              <p className="text-xl font-semibold text-[var(--color-text)] leading-relaxed pattern-template">
                {pattern.template.split(/(\{[^}]+\}|\*)/g).map((part, i) => {
                  const isSlot = (part.startsWith('{') && part.endsWith('}')) || part === '*';
                  if (isSlot) {
                    return <span key={i} className="slot-placeholder mx-0.5">{part}</span>;
                  }
                  return <span key={i}>{part}</span>;
                })}
              </p>
            </div>

            {/* Slots legend */}
            {parseSlots(pattern.template).length > 0 && (
              <div className="mb-6">
                <p className="text-xs text-[var(--color-text-muted)] mb-2">填槽说明</p>
                <div className="space-y-2">
                  {parseSlots(pattern.template).map((slot) => (
                    <div key={slot.name} className="flex items-center gap-3 text-sm">
                      <code className="px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 font-mono text-xs">
                        {`{${slot.name}}`}
                      </code>
                      <span className="text-[var(--color-text-muted)]">→ 填入相关内容</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* First example */}
            {pattern.examples?.[0] && (
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-2">典型例句</p>
                <blockquote className="pl-4 border-l-2 border-indigo-400 text-[var(--color-text)] leading-relaxed"
                  style={{ fontFamily: "'Noto Serif SC', serif" }}>
                  {pattern.examples[0].text}
                </blockquote>
              </div>
            )}
          </div>
        </div>
      </div>

      <hr className="ink-rule mb-12" />

      {/* Examples section */}
      <div className="animate-fade-up" style={{ animationDelay: '0.2s' }}>
        <ExamplesList patternId={id} />
      </div>
    </div>
  );
}

// ─── Mock examples ────────────────────────────────────────────────────────────

const MOCK_EXAMPLES: Example[] = [
  { id: 1, pattern_id: 1, text: '只有努力学习才能取得好成绩', source: 'Bilibili评论区', likes: 2341 },
  { id: 2, pattern_id: 1, text: '只有先睡着才能梦见涨工资', source: '微博', likes: 1892 },
  { id: 3, pattern_id: 1, text: '只有躺平才能不被卷死', source: 'Bilibili', likes: 1543 },
  { id: 4, pattern_id: 1, text: '只有真正经历过才能理解其中的苦', source: '知乎', likes: 987 },
  { id: 5, pattern_id: 1, text: '只有失去了才知道珍惜', source: '评论区', likes: 756 },
];
