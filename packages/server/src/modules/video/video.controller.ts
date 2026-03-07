import express from 'express';

const router = express.Router();

// 模拟数据
const videos = [
  {
    id: 1,
    bvid: 'BV1xx411c7mD',
    aid: 123456789,
    title: '【道听途说169下】三霄娘娘抱走我的孩子后许诺我家女娃三代平安',
    description: '本期道听途说讲述了多个灵异故事，包括三霄娘娘、悉尼蓝山巨人等...',
    coverUrl: 'https://i0.hdslb.com/bfs/archive/8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a.jpg',
    duration: 2683,
    pubDate: '2026-02-28T00:00:00Z',
    viewCount: 448000,
    danmakuCount: 2547,
    commentCount: 3081,
    seriesName: '道听途说',
    episodeNumber: 169,
  },
  {
    id: 2,
    bvid: 'BV1xx411c7mE',
    aid: 123456790,
    title: '【道听途说169上】病患脑部开刀血液溅入医学生眼睛',
    description: '本期道听途说讲述了医学生的恐怖经历，以及其他灵异故事...',
    coverUrl: 'https://i1.hdslb.com/bfs/archive/9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f.jpg',
    duration: 2642,
    pubDate: '2026-02-27T00:00:00Z',
    viewCount: 477000,
    danmakuCount: 3126,
    commentCount: 3118,
    seriesName: '道听途说',
    episodeNumber: 169,
  },
];

// 获取视频详情
router.get('/videos/:bvid', (req, res) => {
  const { bvid } = req.params;
  const video = videos.find(v => v.bvid === bvid);
  
  if (!video) {
    return res.status(404).json({
      code: 404,
      message: '视频不存在',
    });
  }
  
  res.json({
    code: 200,
    data: video,
  });
});

// 获取视频列表
router.get('/videos', (req, res) => {
  const { page = 1, pageSize = 10, series } = req.query;
  
  let filteredVideos = videos;
  if (series) {
    filteredVideos = videos.filter(v => v.seriesName === series);
  }
  
  const start = (Number(page) - 1) * Number(pageSize);
  const end = start + Number(pageSize);
  const paginatedVideos = filteredVideos.slice(start, end);
  
  res.json({
    code: 200,
    data: {
      list: paginatedVideos,
      pagination: {
        page: Number(page),
        pageSize: Number(pageSize),
        total: filteredVideos.length,
        totalPages: Math.ceil(filteredVideos.length / Number(pageSize)),
      },
    },
  });
});

module.exports = router;