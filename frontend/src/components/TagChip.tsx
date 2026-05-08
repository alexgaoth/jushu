'use client';

import Link from 'next/link';
import type { Tag } from '@/lib/api';

// Predefined palette cycling for tags without explicit colors
const TAG_PALETTE = [
  'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-800/60',
  'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-800/60',
  'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 hover:bg-rose-200 dark:hover:bg-rose-800/60',
  'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-800/60',
  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 hover:bg-emerald-200 dark:hover:bg-emerald-800/60',
  'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300 hover:bg-sky-200 dark:hover:bg-sky-800/60',
  'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-800/60',
  'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300 hover:bg-teal-200 dark:hover:bg-teal-800/60',
];

function getTagColor(id: number): string {
  return TAG_PALETTE[id % TAG_PALETTE.length];
}

interface TagChipProps {
  tag: Tag;
  size?: 'sm' | 'md';
  clickable?: boolean;
  onClick?: (tag: Tag) => void;
  active?: boolean;
}

export function TagChip({ tag, size = 'sm', clickable = true, onClick, active = false }: TagChipProps) {
  const colorClass = active
    ? 'bg-indigo-500 text-white hover:bg-indigo-600'
    : getTagColor(tag.id);

  const sizeClass = size === 'sm'
    ? 'text-xs px-2 py-0.5'
    : 'text-sm px-3 py-1';

  const baseClass = `inline-flex items-center rounded-full font-medium transition-colors duration-150 cursor-pointer ${colorClass} ${sizeClass}`;

  if (onClick) {
    return (
      <button
        type="button"
        className={baseClass}
        onClick={() => onClick(tag)}
      >
        {tag.name}
        {tag.count !== undefined && (
          <span className="ml-1 opacity-60 text-[10px]">{tag.count}</span>
        )}
      </button>
    );
  }

  if (clickable) {
    return (
      <Link
        href={`/browse?tag=${tag.slug}`}
        className={baseClass}
      >
        {tag.name}
        {tag.count !== undefined && (
          <span className="ml-1 opacity-60 text-[10px]">{tag.count}</span>
        )}
      </Link>
    );
  }

  return (
    <span className={baseClass}>
      {tag.name}
    </span>
  );
}

interface TagListProps {
  tags: Tag[];
  size?: 'sm' | 'md';
  max?: number;
  onTagClick?: (tag: Tag) => void;
  activeTag?: string;
}

export function TagList({ tags, size = 'sm', max, onTagClick, activeTag }: TagListProps) {
  const displayed = max ? tags.slice(0, max) : tags;
  const remaining = max ? Math.max(0, tags.length - max) : 0;

  return (
    <div className="flex flex-wrap gap-1">
      {displayed.map((tag) => (
        <TagChip
          key={tag.id}
          tag={tag}
          size={size}
          onClick={onTagClick}
          active={activeTag === tag.slug}
          clickable={!onTagClick}
        />
      ))}
      {remaining > 0 && (
        <span className={`inline-flex items-center rounded-full bg-[var(--color-border)] text-[var(--color-text-muted)] font-medium ${size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1'}`}>
          +{remaining}
        </span>
      )}
    </div>
  );
}
