import type { Pattern } from '@/lib/api';

export const MOCK_PATTERN_DATA: Record<number, Pattern> = {
  1: {
    id: 1,
    template: '只有{slot1}才能{slot2}',
    example_count: 1842,
    usage_count: 9201,
    created_at: '2024-01-01',
    tags: [
      { id: 1, name: '强调', slug: '强调' },
      { id: 2, name: '逻辑', slug: '逻辑' },
    ],
    examples: [
      { id: 1, pattern_id: 1, text: '只有努力学习才能取得好成绩', source: 'Bilibili' },
      { id: 2, pattern_id: 1, text: '只有先睡着才能梦见涨工资', source: '微博' },
    ],
  },
  2: {
    id: 2,
    template: '不是{slot1}，而是{slot2}',
    example_count: 2341,
    usage_count: 11205,
    created_at: '2024-01-02',
    tags: [
      { id: 3, name: '对比', slug: '对比' },
      { id: 4, name: '纠正', slug: '纠正' },
    ],
    examples: [
      { id: 3, pattern_id: 2, text: '不是我不努力，而是对手太强了', source: 'Bilibili' },
    ],
  },
  3: {
    id: 3,
    template: '{slot1}的尽头是{slot2}',
    example_count: 892,
    usage_count: 4320,
    created_at: '2024-01-03',
    tags: [
      { id: 5, name: '哲学', slug: '哲学' },
      { id: 6, name: '感悟', slug: '感悟' },
    ],
    examples: [
      { id: 5, pattern_id: 3, text: '卷的尽头是躺平', source: 'Bilibili' },
      { id: 6, pattern_id: 3, text: '内卷的尽头是出走', source: '微博' },
    ],
  },
};
