import dotenv from 'dotenv';
import { BilibiliCrawler } from './sites/bilibili';
import { Scheduler } from './core/scheduler';

// 加载环境变量
dotenv.config();

console.log('怖客爬虫服务启动...');

// 初始化B站爬虫
const bilibiliCrawler = new BilibiliCrawler({
  channelId: '28346875', // 大佬何金银的B站空间ID
  seriesFilter: '道听途说',
  maxVideos: 50,
  rateLimit: {
    requestsPerSecond: 2,
    concurrentRequests: 3,
  },
});

// 初始化调度器
const scheduler = new Scheduler({
  crawlers: [bilibiliCrawler],
  schedule: {
    initialCrawl: true,
    incrementalCrawl: '0 2 * * *', // 每天凌晨2点
    fullCrawl: '0 3 * * 0', // 每周日凌晨3点
  },
});

// 启动服务
scheduler.start().then(() => {
  console.log('爬虫服务启动成功');
}).catch((error) => {
  console.error('爬虫服务启动失败:', error);
  process.exit(1);
});

// 处理进程退出
process.on('SIGINT', () => {
  console.log('正在停止爬虫服务...');
  scheduler.stop().then(() => {
    console.log('爬虫服务已停止');
    process.exit(0);
  });
});