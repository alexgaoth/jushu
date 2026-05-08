import type { Pattern } from '@/lib/api';

export const MOCK_PATTERN_DATA: Record<number, Pattern> = {
  1: {
    id: 1,
    template: '只有{A}才能{B}',
    description: '强调条件与结果之间的必要关系，常用于表达唯一路径或强调因果逻辑。',
    example_count: 1842,
    usage_count: 9201,
    created_at: '2024-01-01',
    tags: [
      { id: 1, name: '强调', slug: '强调' },
      { id: 2, name: '逻辑', slug: '逻辑' },
      { id: 11, name: '条件句', slug: '条件句' },
    ],
    examples: [
      { id: 1, pattern_id: 1, text: '只有努力学习才能取得好成绩', source: 'Bilibili', likes: 2341 },
      { id: 2, pattern_id: 1, text: '只有先睡着才能梦见涨工资', source: '微博', likes: 1892 },
    ],
  },
  2: {
    id: 2,
    template: '不是{A}，而是{B}',
    description: '纠正误解，通过否定一种解释来强调另一种更准确的表达。常见于辩驳和澄清场景。',
    example_count: 2341,
    usage_count: 11205,
    created_at: '2024-01-02',
    tags: [
      { id: 3, name: '对比', slug: '对比' },
      { id: 4, name: '纠正', slug: '纠正' },
    ],
    examples: [
      { id: 3, pattern_id: 2, text: '不是我不努力，而是对手太强了', source: 'Bilibili评论', likes: 3201 },
    ],
  },
  3: {
    id: 3,
    template: '{A}的尽头是{B}',
    description: '哲学感强烈的句式，描述某种行为或状态的最终归宿，常带有反讽或感悟色彩。',
    example_count: 892,
    usage_count: 4320,
    created_at: '2024-01-03',
    tags: [
      { id: 5, name: '哲学', slug: '哲学' },
      { id: 6, name: '感悟', slug: '感悟' },
    ],
    examples: [
      { id: 5, pattern_id: 3, text: '卷的尽头是躺平', source: 'Bilibili', likes: 8923 },
      { id: 6, pattern_id: 3, text: '内卷的尽头是出走', source: '微博', likes: 4521 },
    ],
  },
};
