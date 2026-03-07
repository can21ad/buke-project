import express from 'express';

const router = express.Router();

// 模拟爬虫状态
let crawlerStatus = {
  running: false,
  lastRun: '2026-03-01T00:00:00Z',
  nextRun: '2026-03-05T02:00:00Z',
  progress: 0,
  currentTask: 'idle',
};

// 获取爬虫状态
router.get('/crawler/status', (req, res) => {
  res.json({
    code: 200,
    data: crawlerStatus,
  });
});

// 触发爬虫任务
router.post('/crawler/trigger', (req, res) => {
  const { type = 'incremental' } = req.body;
  
  // 模拟爬虫启动
  crawlerStatus = {
    ...crawlerStatus,
    running: true,
    currentTask: type,
    progress: 0,
  };
  
  console.log(`触发爬虫任务: ${type}`);
  
  // 模拟爬虫进度
  setTimeout(() => {
    crawlerStatus = {
      ...crawlerStatus,
      running: false,
      lastRun: new Date().toISOString(),
      progress: 100,
      currentTask: 'idle',
    };
  }, 5000);
  
  res.json({
    code: 200,
    message: `爬虫任务已启动: ${type}`,
  });
});

module.exports = router;