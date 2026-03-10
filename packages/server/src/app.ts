import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

// 创建Express应用
const app = express();

// 中间件
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

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