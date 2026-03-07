import express from 'express';

const router = express.Router();

// 模拟数据
const stories = [
  {
    id: 1,
    title: '三霄娘娘抱走我的孩子后许诺我家女娃三代平安',
    summary: '一个关于民间信仰与神秘力量的故事，讲述者描述了三霄娘娘的传说...',
    aiComment: '这是一个关于民间信仰与神秘力量的故事，讲述者描述了三霄娘娘的传说，细节丰富，让人不禁思考：这究竟是神灵庇佑，还是另有隐情？故事氛围营造到位，情节引人入胜，值得细细品味。',
    heatScore: 1234.56,
    mentionCount: 89,
    likeCount: 5678,
    commentCount: 234,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169下】三霄娘娘抱走我的孩子',
      cover: 'https://i0.hdslb.com/bfs/archive/8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a.jpg',
      duration: 2683,
    },
    timeInfo: {
      startTime: 754,
      endTime: 1200,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=754&p=1',
    },
    tags: ['灵异', '民间传说', '真实经历', '细思极恐'],
    relatedStories: [2, 3, 4],
    comments: [
      {
        id: 1,
        username: '用户A',
        content: '这个故事真的绝了，求出处！',
        likeCount: 123,
        replyCount: 5,
        time: '2026-03-01',
      },
      {
        id: 2,
        username: '用户B',
        content: '类似的还有那个XX故事，也很精彩...',
        likeCount: 89,
        replyCount: 3,
        time: '2026-03-02',
      },
    ],
  },
  {
    id: 2,
    title: '悉尼蓝山深处的恐怖巨人',
    summary: '澳洲蓝山的神秘巨人传说，露营者的恐怖遭遇...',
    aiComment: '澳洲蓝山的神秘巨人传说，露营者的恐怖遭遇让人心跳加速。故事氛围紧张，细节描写到位，仿佛身临其境。这样的真实经历总是让人既害怕又好奇。',
    heatScore: 987.45,
    mentionCount: 67,
    likeCount: 4321,
    commentCount: 189,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169下】悉尼蓝山深处的恐怖巨人',
      cover: 'https://i1.hdslb.com/bfs/archive/9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f.jpg',
      duration: 2683,
    },
    timeInfo: {
      startTime: 1200,
      endTime: 1600,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=1200&p=1',
    },
    tags: ['恐怖', '国外', '真实经历', '巨人'],
    relatedStories: [1, 3, 5],
    comments: [
      {
        id: 1,
        username: '用户C',
        content: '蓝山真的有巨人传说，我之前也听说过！',
        likeCount: 98,
        replyCount: 2,
        time: '2026-03-01',
      },
    ],
  },
  {
    id: 3,
    title: '病患脑部开刀血液溅入医学生眼睛',
    summary: '医学生在手术中意外接触到病患血液，从此世界变得不同...',
    aiComment: '医学生的恐怖经历，血液溅入眼睛后看到的世界截然不同。这个故事充满了悬疑和恐怖元素，让人不禁思考医学与超自然的边界。',
    heatScore: 876.34,
    mentionCount: 56,
    likeCount: 3456,
    commentCount: 156,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169上】病患脑部开刀血液溅入医学生眼睛',
      cover: 'https://i2.hdslb.com/bfs/archive/8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a.jpg',
      duration: 2683,
    },
    timeInfo: {
      startTime: 300,
      endTime: 700,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=300&p=1',
    },
    tags: ['医院', '灵异', '细思极恐'],
    relatedStories: [1, 2, 4],
    comments: [],
  },
];

// 获取故事列表
router.get('/stories', (req, res) => {
  const { page = 1, pageSize = 20, sortBy = 'heat' } = req.query;
  
  // 排序
  let sortedStories = [...stories];
  switch (sortBy) {
    case 'heat':
      sortedStories.sort((a, b) => b.heatScore - a.heatScore);
      break;
    case 'mention':
      sortedStories.sort((a, b) => b.mentionCount - a.mentionCount);
      break;
    default:
      break;
  }
  
  // 分页
  const start = (Number(page) - 1) * Number(pageSize);
  const end = start + Number(pageSize);
  const paginatedStories = sortedStories.slice(start, end);
  
  res.json({
    code: 200,
    data: {
      list: paginatedStories,
      pagination: {
        page: Number(page),
        pageSize: Number(pageSize),
        total: stories.length,
        totalPages: Math.ceil(stories.length / Number(pageSize)),
      },
    },
  });
});

// 获取故事详情
router.get('/stories/:id', (req, res) => {
  const { id } = req.params;
  const story = stories.find(s => s.id === Number(id));
  
  if (!story) {
    return res.status(404).json({
      code: 404,
      message: '故事不存在',
    });
  }
  
  res.json({
    code: 200,
    data: story,
  });
});

// 获取热门故事TOP10
router.get('/stories/hot', (req, res) => {
  const hotStories = [...stories]
    .sort((a, b) => b.heatScore - a.heatScore)
    .slice(0, 10)
    .map((story, index) => ({
      ...story,
      rank: index + 1,
    }));
  
  res.json({
    code: 200,
    data: {
      list: hotStories,
      updatedAt: new Date().toISOString(),
    },
  });
});

// 故事点击记录
router.post('/stories/:id/click', (req, res) => {
  const { id } = req.params;
  const { action } = req.body;
  
  console.log(`故事 ${id} 被点击，动作: ${action}`);
  
  res.json({
    code: 200,
    message: '记录成功',
  });
});

module.exports = router;