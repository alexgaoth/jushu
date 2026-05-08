const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Frontend types (used by components) ─────────────────────────────────────

export interface Tag {
  id: number;
  name: string;
  slug: string;
  category?: string;
  count?: number;
}

export interface Example {
  id: number;
  pattern_id: number;
  text: string;
  source?: string;
}

export interface Pattern {
  id: number;
  template: string;
  tags: Tag[];
  examples: Example[];
  example_count: number;
  usage_count: number;
  created_at: string;
}

export interface SearchResult {
  items: Pattern[];
  total: number;
  page: number;
  size: number;
  pages: number;
  query: string;
}

export interface TrendingResult {
  items: Pattern[];
  range: string;
}

export interface GenerateResult {
  sentence: string;
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

// ─── API response shapes (what the backend actually returns) ──────────────────

interface ApiTag {
  id: number;
  name: string;
  category: string;
  pattern_count?: number;
}

interface ApiPatternSummary {
  id: number;
  template_text: string;
  source_count: number;
  example_count: number;
  example: string | null;
  tags: ApiTag[];
}

interface ApiSearchResponse {
  total: number;
  page: number;
  size: number;
  results: ApiPatternSummary[];
}

interface ApiTrendingResponse {
  range: string;
  results: ApiPatternSummary[];
}

interface ApiTagsResponse {
  total: number;
  tags: ApiTag[];
}

interface ApiPatternDetail {
  id: number;
  template_text: string;
  source_count: number;
  example_count: number;
  tags: ApiTag[];
  examples: Array<{ id: number; content: string; slot_fillings: Record<string, string> | null }>;
  created_at: string;
}

interface ApiExamplesResponse {
  total: number;
  page: number;
  size: number;
  examples: Array<{ id: number; pattern_id: number; content: string; slot_fillings: Record<string, string> | null }>;
}

interface ApiGenerateResponse {
  sentence: string;
}

// ─── Normalisers ─────────────────────────────────────────────────────────────

function normaliseTag(t: ApiTag): Tag {
  return { id: t.id, name: t.name, slug: t.name, category: t.category, count: t.pattern_count };
}

function normaliseSummary(p: ApiPatternSummary): Pattern {
  return {
    id: p.id,
    template: p.template_text,
    tags: (p.tags || []).map(normaliseTag),
    examples: p.example ? [{ id: 0, pattern_id: p.id, text: p.example }] : [],
    example_count: p.example_count ?? 0,
    usage_count: p.source_count ?? 0,
    created_at: '',
  };
}

function normaliseDetail(p: ApiPatternDetail): Pattern {
  return {
    id: p.id,
    template: p.template_text,
    tags: (p.tags || []).map(normaliseTag),
    examples: (p.examples || []).map((e) => ({
      id: e.id,
      pattern_id: p.id,
      text: e.content,
    })),
    example_count: p.example_count ?? 0,
    usage_count: p.source_count ?? 0,
    created_at: p.created_at ?? '',
  };
}

// ─── HTTP helper ──────────────────────────────────────────────────────────────

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.toString(), {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ─── Public API functions ─────────────────────────────────────────────────────

export async function searchPatterns(q: string, page = 1, size = 20): Promise<SearchResult> {
  const raw = await get<ApiSearchResponse>('/api/search', { q, page, size });
  const results = raw.results || [];
  const pages = raw.total > 0 ? Math.ceil(raw.total / (raw.size || size)) : 1;
  return {
    items: results.map(normaliseSummary),
    total: raw.total,
    page: raw.page,
    size: raw.size,
    pages,
    query: q,
  };
}

export async function getTrending(range = 'week'): Promise<TrendingResult> {
  const raw = await get<ApiTrendingResponse>('/api/trending', { range });
  return {
    range: raw.range,
    items: (raw.results || []).map(normaliseSummary),
  };
}

export async function getPattern(id: number): Promise<Pattern> {
  const raw = await get<ApiPatternDetail>(`/api/patterns/${id}`);
  return normaliseDetail(raw);
}

export async function getTags(): Promise<Tag[]> {
  const raw = await get<ApiTagsResponse>('/api/tags');
  return (raw.tags || []).map(normaliseTag);
}

export async function generateFromPattern(
  id: number,
  slots: Record<string, string>
): Promise<GenerateResult> {
  const params: Record<string, string> = {};
  Object.entries(slots).forEach(([k, v]) => { params[k] = v; });
  const raw = await get<ApiGenerateResponse>(`/api/patterns/${id}/generate`, params);
  return { sentence: raw.sentence };
}

export async function getExamples(patternId: number, page = 1, sort = 'hot'): Promise<ExamplesResult> {
  const raw = await get<ApiExamplesResponse>('/api/examples', { pattern_id: patternId, page, sort });
  return {
    total: raw.total,
    page: raw.page,
    size: raw.size,
    items: (raw.examples || []).map((e) => ({
      id: e.id,
      pattern_id: patternId,
      text: e.content,
    })),
  };
}

export async function browsePatterns(page = 1, size = 24, tag?: string, sort = 'hot'): Promise<BrowseResult> {
  const raw = await get<ApiSearchResponse>('/api/search', { q: tag || '', page, size });
  const results = raw.results || [];
  const pages = raw.total > 0 ? Math.ceil(raw.total / (raw.size || size)) : 1;
  return {
    items: results.map(normaliseSummary),
    total: raw.total,
    page: raw.page,
    size: raw.size,
    pages,
  };
}

// ─── Template utilities ───────────────────────────────────────────────────────

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
