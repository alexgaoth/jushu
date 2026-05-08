const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Tag {
  id: number;
  name: string;
  slug: string;
  color?: string;
  count?: number;
}

export interface Example {
  id: number;
  pattern_id: number;
  text: string;
  source?: string;
  likes?: number;
  created_at?: string;
}

export interface Pattern {
  id: number;
  template: string;
  description?: string;
  tags: Tag[];
  examples: Example[];
  example_count: number;
  usage_count: number;
  created_at: string;
  updated_at?: string;
  trending_score?: number;
}

export interface SearchResult {
  items: Pattern[];
  total: number;
  page: number;
  size: number;
  pages: number;
  query: string;
}

export interface GenerateResult {
  text: string;
  pattern_id: number;
  slots: Record<string, string>;
}

export interface TrendingResult {
  items: Pattern[];
  range: string;
}

export interface ExamplesResult {
  items: Example[];
  total: number;
  page: number;
  size: number;
}

export interface BrowseResult {
  items: Pattern[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ─── HTTP helpers ─────────────────────────────────────────────────────────────

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        url.searchParams.set(k, String(v));
      }
    });
  }
  const res = await fetch(url.toString(), {
    headers: { 'Accept': 'application/json' },
    next: { revalidate: 30 },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ─── API functions ────────────────────────────────────────────────────────────

export async function searchPatterns(
  q: string,
  page: number = 1,
  size: number = 20
): Promise<SearchResult> {
  return get<SearchResult>('/api/search', { q, page, size });
}

export async function getPattern(id: number): Promise<Pattern> {
  return get<Pattern>(`/api/patterns/${id}`);
}

export async function generateFromPattern(
  id: number,
  slots: Record<string, string>
): Promise<GenerateResult> {
  return post<GenerateResult>(`/api/patterns/${id}/generate`, { slots });
}

export async function getTags(): Promise<Tag[]> {
  return get<Tag[]>('/api/tags');
}

export async function getTrending(range: string = 'week'): Promise<TrendingResult> {
  return get<TrendingResult>('/api/trending', { range });
}

export async function getExamples(
  patternId: number,
  page: number = 1,
  sort: string = 'likes'
): Promise<ExamplesResult> {
  return get<ExamplesResult>(`/api/patterns/${patternId}/examples`, { page, sort });
}

export async function browsePatterns(
  page: number = 1,
  size: number = 24,
  tag?: string,
  sort: string = 'usage'
): Promise<BrowseResult> {
  return get<BrowseResult>('/api/patterns', { page, size, tag, sort });
}

// ─── Template parsing ─────────────────────────────────────────────────────────

export interface SlotInfo {
  name: string;
  label: string;
  index: number;
}

export function parseSlots(template: string): SlotInfo[] {
  const regex = /\{([^}]+)\}/g;
  const seen = new Set<string>();
  const slots: SlotInfo[] = [];
  let index = 0;
  let match;
  while ((match = regex.exec(template)) !== null) {
    const name = match[1];
    if (!seen.has(name)) {
      seen.add(name);
      slots.push({ name, label: name, index: index++ });
    }
  }
  return slots;
}

export function fillTemplate(template: string, values: Record<string, string>): string {
  return template.replace(/\{([^}]+)\}/g, (_, name) => values[name] || `{${name}}`);
}
