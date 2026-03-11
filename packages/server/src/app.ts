import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

// 创建Express应用
const app = express();

// 防盗用配置
const API_KEY = process.env.API_KEY || 'your-secure-api-key';
const RATE_LIMIT_WINDOW = 60000; // 1分钟
const RATE_LIMIT_MAX = 60; // 每分钟最多60个请求
const BLACKLIST = new Set<string>();
const REQUESTS = new Map<string, { count: number; lastReset: number }>();

// 中间件
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API密钥验证中间件
const apiKeyAuth = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const apiKey = req.headers['x-api-key'] as string;
  
  if (!apiKey) {
    return res.status(401).json({
      code: 401,
      message: '缺少API密钥',
    });
  }
  
  if (apiKey !== API_KEY) {
    return res.status(401).json({
      code: 401,
      message: '无效的API密钥',
    });
  }
  
  next();
};

// 请求频率限制中间件
const rateLimit = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const ip = req.ip || req.connection.remoteAddress || '';
  
  // 检查黑名单
  if (BLACKLIST.has(ip)) {
    return res.status(403).json({
      code: 403,
      message: '您的IP已被限制访问',
    });
  }
  
  // 检查并更新请求计数
  const now = Date.now();
  const requestInfo = REQUESTS.get(ip);
  
  if (requestInfo) {
    // 检查是否需要重置计数
    if (now - requestInfo.lastReset > RATE_LIMIT_WINDOW) {
      REQUESTS.set(ip, { count: 1, lastReset: now });
    } else {
      // 检查是否超过限制
      if (requestInfo.count >= RATE_LIMIT_MAX) {
        // 添加到黑名单
        BLACKLIST.add(ip);
        console.warn(`[RATE LIMIT] IP ${ip} has been blacklisted`);
        return res.status(429).json({
          code: 429,
          message: '请求过于频繁，请稍后再试',
        });
      }
      // 增加计数
      REQUESTS.set(ip, { count: requestInfo.count + 1, lastReset: requestInfo.lastReset });
    }
  } else {
    // 第一次请求
    REQUESTS.set(ip, { count: 1, lastReset: now });
  }
  
  next();
};

// 全局防盗用中间件
app.use('/api', apiKeyAuth);
app.use('/api', rateLimit);

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: '怖客服务运行正常' });
});

// API路由
app.use('/api/v1', require('./modules/story/story.controller'));
app.use('/api/v1', require('./modules/video/video.controller'));
app.use('/api/v1', require('./modules/crawler/crawler.controller'));
app.use('/api/v1', require('./modules/search/search.controller'));
app.use('/api/v1', require('./modules/summarizer/summarizer.controller'));

// 404处理
app.use('*', (req, res) => {
  res.status(404).json({
    code: 404,
    message: '接口不存在',
  });
});

// 错误处理
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    code: 500,
    message: '服务器内部错误',
  });
});

// 启动服务器
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`服务器运行在 http://localhost:${PORT}`);
});

export default app;