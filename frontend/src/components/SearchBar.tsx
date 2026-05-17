'use client';

import { useRef, useEffect, useCallback } from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch?: (value: string) => void;
  placeholder?: string;
  size?: 'sm' | 'lg';
  autoFocus?: boolean;
  className?: string;
}

export function SearchBar({
  value,
  onChange,
  onSearch,
  placeholder = '搜索 JuShi，例如：感谢*让我*',
  size = 'lg',
  autoFocus = false,
  className = '',
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      onChange(val);

      if (onSearch) {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
          onSearch(val);
        }, 300);
      }
    },
    [onChange, onSearch]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && onSearch) {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      onSearch(value);
    }
    if (e.key === 'Escape') {
      onChange('');
      if (onSearch) onSearch('');
    }
  };

  const handleClear = () => {
    onChange('');
    if (onSearch) onSearch('');
    inputRef.current?.focus();
  };

  const isLarge = size === 'lg';

  return (
    <div className={`relative group ${className}`}>
      {/* Search icon */}
      <div className={`absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] pointer-events-none transition-colors group-focus-within:text-indigo-400 ${isLarge ? 'text-xl' : 'text-base'}`}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={isLarge ? 'w-6 h-6' : 'w-4 h-4'}
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
      </div>

      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={`
          w-full bg-[var(--color-surface)] border border-[var(--color-border)]
          rounded-2xl text-[var(--color-text)] placeholder-[var(--color-text-muted)]
          focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20
          transition-all duration-200
          shadow-card hover:shadow-card-hover focus:shadow-card-hover
          ${isLarge ? 'pl-14 pr-12 py-4 text-lg' : 'pl-10 pr-10 py-2.5 text-sm'}
        `}
        style={{ fontFamily: "'Noto Serif SC', 'STSong', serif" }}
        spellCheck={false}
        autoComplete="off"
      />

      {/* Wildcard hint */}
      {isLarge && !value && (
        <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1.5 pointer-events-none">
          <span className="text-xs text-[var(--color-text-muted)] bg-[var(--color-border)] px-2 py-0.5 rounded font-mono opacity-60">*</span>
          <span className="text-xs text-[var(--color-text-muted)] opacity-50">通配符</span>
        </div>
      )}

      {/* Clear button */}
      {value && (
        <button
          type="button"
          onClick={handleClear}
          className={`absolute top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors rounded-full p-0.5 hover:bg-[var(--color-border)] ${isLarge ? 'right-4' : 'right-3'}`}
          aria-label="清除搜索"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      )}

      {/* Bottom glow effect on focus */}
      <div className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 shadow-glow" />
    </div>
  );
}
