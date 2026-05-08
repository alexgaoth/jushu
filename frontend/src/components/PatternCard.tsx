'use client';

import Link from 'next/link';
import type { Pattern } from '@/lib/api';
import { TagList } from './TagChip';

interface PatternCardProps {
  pattern: Pattern;
  style?: React.CSSProperties;
  className?: string;
}

// Render template with slots highlighted
function TemplateDisplay({ template }: { template: string }) {
  const parts = template.split(/(\{[^}]+\}|\*)/g);

  return (
    <span className="pattern-template">
      {parts.map((part, i) => {
        if (part === '*' || (part.startsWith('{') && part.endsWith('}'))) {
          const label = part === '*' ? '___' : part.slice(1, -1);
          return (
            <span key={i} className="slot-placeholder mx-0.5">
              {label}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}

export function PatternCard({ pattern, style, className = '' }: PatternCardProps) {
  const firstExample = pattern.examples?.[0];

  return (
    <Link
      href={`/pattern/${pattern.id}`}
      className={`
        group block p-5 rounded-2xl border border-[var(--color-border)]
        bg-[var(--color-surface)] shadow-card hover:shadow-card-hover
        transition-all duration-300 hover:-translate-y-0.5
        ${className}
      `}
      style={style}
    >
      {/* Pattern template */}
      <div className="mb-3">
        <p className="text-base sm:text-lg font-semibold text-[var(--color-text)] leading-relaxed group-hover:text-indigo-500 transition-colors duration-200">
          <TemplateDisplay template={pattern.template} />
        </p>
      </div>

      {/* Example sentence */}
      {firstExample && (
        <div className="mb-4 pl-3 border-l-2 border-[var(--color-border)] group-hover:border-indigo-300 transition-colors duration-200">
          <p className="text-sm text-[var(--color-text-muted)] line-clamp-2 leading-relaxed">
            {firstExample.text}
          </p>
        </div>
      )}

      {/* Footer: tags + count */}
      <div className="flex items-end justify-between gap-2">
        <TagList tags={pattern.tags} max={3} size="sm" />

        <div className="flex items-center gap-3 shrink-0">
          {pattern.example_count > 0 && (
            <span className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              {pattern.example_count.toLocaleString()}
            </span>
          )}
          {pattern.usage_count > 0 && (
            <span className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              {pattern.usage_count.toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

// Skeleton loader for pattern card
export function PatternCardSkeleton() {
  return (
    <div className="p-5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-card">
      <div className="skeleton h-6 rounded-lg mb-3 w-4/5" />
      <div className="skeleton h-4 rounded mb-1.5 w-full" />
      <div className="skeleton h-4 rounded mb-4 w-2/3" />
      <div className="flex gap-2">
        <div className="skeleton h-5 rounded-full w-14" />
        <div className="skeleton h-5 rounded-full w-16" />
        <div className="skeleton h-5 rounded-full w-12" />
      </div>
    </div>
  );
}
