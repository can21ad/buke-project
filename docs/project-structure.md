# 怖客项目目录结构

```
buke/
├── docs/                          # 项目文档
│   ├── architecture.md            # 架构设计文档
│   ├── api.md                     # API接口文档
│   └── deployment.md              # 部署文档
│
├── packages/                      # Monorepo包管理
│   │
│   ├── web/                       # 前端应用
│   │   ├── src/
│   │   │   ├── app/               # Next.js App Router
│   │   │   │   ├── layout.tsx     # 根布局
│   │   │   │   ├── page.tsx       # 首页
│   │   │   │   ├── stories/       # 故事相关页面
│   │   │   │   │   ├── page.tsx   # 故事列表
│   │   │   │   │   └── [id]/      # 故事详情
│   │   │   │   │       └── page.tsx
│   │   │   │   └── search/        # 搜索页面
│   │   │   │       └── page.tsx
│   │   │   │
│   │   │   ├── components/        # 组件目录
│   │   │   │   ├── ui/            # 基础UI组件
│   │   │   │   │   ├── Button/
│   │   │   │   │   ├── Card/
│   │   │   │   │   ├── Input/
│   │   │   │   │   ├── Modal/
│   │   │   │   │   └── Skeleton/
│   │   │   │   │
│   │   │   │   ├── layout/        # 布局组件
│   │   │   │   │   ├── Header/
│   │   │   │   │   ├── Footer/
│   │   │   │   │   └── Sidebar/
│   │   │   │   │
│   │   │   │   ├── story/         # 故事相关组件
│   │   │   │   │   ├── StoryCard/
│   │   │   │   │   ├── StoryList/
│   │   │   │   │   ├── StoryDetail/
│   │   │   │   │   ├── HotRanking/
│   │   │   │   │   └── JumpButton/
│   │   │   │   │
│   │   │   │   ├── search/        # 搜索相关组件
│   │   │   │   │   ├── SearchBar/
│   │   │   │   │   ├── SearchResults/
│   │   │   │   │   └── FilterPanel/
│   │   │   │   │
│   │   │   │   └── comment/       # 评论相关组件
│   │   │   │       ├── CommentCard/
│   │   │   │       └── CommentList/
│   │   │   │
│   │   │   ├── hooks/             # 自定义Hooks
│   │   │   │   ├── useStories.ts
│   │   │   │   ├── useSearch.ts
│   │   │   │   └── useInfiniteScroll.ts
│   │   │   │
│   │   │   ├── stores/            # 状态管理
│   │   │   │   ├── storyStore.ts
│   │   │   │   ├── filterStore.ts
│   │   │   │   └── userStore.ts
│   │   │   │
│   │   │   ├── services/          # API服务
│   │   │   │   ├── api.ts         # API客户端
│   │   │   │   ├── storyService.ts
│   │   │   │   └── searchService.ts
│   │   │   │
│   │   │   ├── types/             # 类型定义
│   │   │   │   ├── story.ts
│   │   │   │   ├── video.ts
│   │   │   │   └── api.ts
│   │   │   │
│   │   │   ├── utils/             # 工具函数
│   │   │   │   ├── format.ts
│   │   │   │   ├── time.ts
│   │   │   │   └── bilibili.ts
│   │   │   │
│   │   │   └── styles/            # 全局样式
│   │   │       ├── globals.css
│   │   │       └── themes/
│   │   │
│   │   ├── public/                # 静态资源
│   │   │   ├── images/
│   │   │   ├── fonts/
│   │   │   └── favicon.ico
│   │   │
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── server/                    # 后端服务
│   │   ├── src/
│   │   │   ├── modules/           # 业务模块
│   │   │   │   ├── story/         # 故事模块
│   │   │   │   │   ├── story.controller.ts
│   │   │   │   │   ├── story.service.ts
│   │   │   │   │   └── story.dto.ts
│   │   │   │   │
│   │   │   │   ├── video/         # 视频模块
│   │   │   │   │   ├── video.controller.ts
│   │   │   │   │   └── video.service.ts
│   │   │   │   │
│   │   │   │   ├── comment/       # 评论模块
│   │   │   │   │   ├── comment.controller.ts
│   │   │   │   │   └── comment.service.ts
│   │   │   │   │
│   │   │   │   ├── search/        # 搜索模块
│   │   │   │   │   ├── search.controller.ts
│   │   │   │   │   └── search.service.ts
│   │   │   │   │
│   │   │   │   └── crawler/       # 爬虫调度模块
│   │   │   │       ├── crawler.controller.ts
│   │   │   │       └── crawler.service.ts
│   │   │   │
│   │   │   ├── services/          # 核心服务
│   │   │   │   ├── cache.service.ts    # 缓存服务
│   │   │   │   ├── queue.service.ts    # 队列服务
│   │   │   │   └── ai.service.ts       # AI简评服务
│   │   │   │
│   │   │   ├── middleware/        # 中间件
│   │   │   │   ├── auth.ts
│   │   │   │   ├── errorHandler.ts
│   │   │   │   └── rateLimiter.ts
│   │   │   │
│   │   │   ├── database/          # 数据库
│   │   │   │   ├── connection.ts
│   │   │   │   ├── migrations/
│   │   │   │   └── seeds/
│   │   │   │
│   │   │   ├── models/            # 数据模型
│   │   │   │   ├── video.model.ts
│   │   │   │   ├── story.model.ts
│   │   │   │   └── comment.model.ts
│   │   │   │
│   │   │   ├── config/            # 配置
│   │   │   │   ├── database.ts
│   │   │   │   ├── redis.ts
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   ├── utils/             # 工具函数
│   │   │   │   ├── logger.ts
│   │   │   │   └── helpers.ts
│   │   │   │
│   │   │   ├── types/             # 类型定义
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   └── app.ts             # 应用入口
│   │   │
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── crawler/                   # 爬虫服务
│   │   ├── src/
│   │   │   ├── sites/             # 各站点爬虫
│   │   │   │   └── bilibili/      # B站爬虫
│   │   │   │       ├── index.ts
│   │   │   │       ├── video.ts       # 视频信息爬取
│   │   │   │       ├── comment.ts     # 评论爬取
│   │   │   │       └── parser.ts      # 数据解析
│   │   │   │
│   │   │   ├── core/              # 爬虫核心
│   │   │   │   ├── scheduler.ts       # 调度器
│   │   │   │   ├── downloader.ts      # 下载器
│   │   │   │   ├── parser.ts          # 解析器基类
│   │   │   │   ├── pipeline.ts        # 数据管道
│   │   │   │   └── queue.ts           # URL队列
│   │   │   │
│   │   │   ├── analyzer/          # 数据分析
│   │   │   │   ├── keyword.ts         # 关键词提取
│   │   │   │   ├── sentiment.ts       # 情感分析
│   │   │   │   ├── heat.ts            # 热度计算
│   │   │   │   └── story.ts           # 故事识别
│   │   │   │
│   │   │   ├── tasks/             # 定时任务
│   │   │   │   ├── daily.ts           # 每日任务
│   │   │   │   ├── hourly.ts          # 每小时任务
│   │   │   │   └── initial.ts         # 初始化任务
│   │   │   │
│   │   │   ├── config/            # 配置
│   │   │   │   ├── sites.ts
│   │   │   │   ├── keywords.ts
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   └── index.ts           # 入口文件
│   │   │
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── shared/                    # 共享代码
│       ├── types/                 # 共享类型
│       │   ├── story.ts
│       │   ├── video.ts
│       │   └── api.ts
│       │
│       ├── constants/             # 常量
│       │   └── index.ts
│       │
│       └── utils/                 # 工具函数
│           └── index.ts
│
├── docker/                        # Docker配置
│   ├── Dockerfile.web
│   ├── Dockerfile.server
│   ├── Dockerfile.crawler
│   └── docker-compose.yml
│
├── scripts/                       # 脚本文件
│   ├── init-db.sql               # 数据库初始化
│   └── deploy.sh                 # 部署脚本
│
├── .gitignore
├── .env.example
├── package.json                   # 根package.json (Monorepo)
├── pnpm-workspace.yaml           # pnpm工作空间配置
└── README.md
```

## 技术栈说明

### 前端
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS + shadcn/ui
- **状态**: Zustand
- **请求**: TanStack Query

### 后端
- **框架**: Express / Fastify
- **语言**: TypeScript
- **数据库**: MySQL 8.0 + TypeORM
- **缓存**: Redis
- **搜索**: Elasticsearch

### 爬虫
- **框架**: Puppeteer + Cheerio
- **调度**: node-cron
- **队列**: Bull (Redis-based)

### 开发工具
- **包管理**: pnpm (Monorepo)
- **构建**: Turborepo
- **代码规范**: ESLint + Prettier
- **提交规范**: Commitlint + Husky
