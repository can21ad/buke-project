import express from 'express';

const router = express.Router();

// 模拟搜索结果
const searchResults = [
  {
    id: 1,
    title: '三霄娘娘抱走我的孩子后许诺我家女娃三代平安',
    summary: '一个关于民间信仰与神秘力量的故事，讲述者描述了三霄娘娘的传说...',
    heatScore: 1234.56,
    mentionCount: 89,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169下】三霄娘娘抱走我的孩子',
      cover: 'https://i0.hdslb.com/bfs/archive/8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a.jpg',
    },
    timeInfo: {
      startTime: 754,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=754&p=1',
    },
    tags: ['灵异', '民间传说', '真实经历'],
  },
  {
    id: 2,
    title: '悉尼蓝山深处的恐怖巨人',
    summary: '澳洲蓝山的神秘巨人传说，露营者的恐怖遭遇...',
    heatScore: 987.45,
    mentionCount: 67,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169下】悉尼蓝山深处的恐怖巨人',
      cover: 'https://i1.hdslb.com/bfs/archive/9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f.jpg',
    },
    timeInfo: {
      startTime: 1200,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=1200&p=1',
    },
    tags: ['恐怖', '国外', '真实经历'],
  },
];

// 搜索故事
router.get('/search', (req, res) => {
  const { keyword, page = 1, pageSize = 20 } = req.query;
  
  console.log(`搜索关键词: ${keyword}`);
  
  // 模拟搜索结果
  const results = searchResults.filter(story => 
    story.title.includes(keyword as string) || 
    story.summary.includes(keyword as string)
  );
  
  const start = (Number(page) - 1) * Number(pageSize);
  const end = start + Number(pageSize);
  const paginatedResults = results.slice(start, end);
  
  res.json({
    code: 200,
    data: {
      list: paginatedResults,
      highlights: [
        {
          field: 'title',
          fragments: [`...${keyword}...`],
        },
      ],
      pagination: {
        page: Number(page),
        pageSize: Number(pageSize),
        total: results.length,
        totalPages: Math.ceil(results.length / Number(pageSize)),
      },
      aggregations: {
        series: [
          { name: '道听途说', count: 2 },
        ],
        tags: [
          { name: '灵异', count: 1 },
          { name: '恐怖', count: 1 },
          { name: '真实经历', count: 2 },
        ],
      },
    },
  });
});

module.exports = router;