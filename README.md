# 怖客 - 恐怖灵异内容聚合平台

## 项目概述

怖客是一款专注于全简中互联网恐怖灵异内容聚合的网页应用，通过爬虫技术收集相关博客评论区数据，筛选用户推荐度高的故事内容进行整合展示。

### MVP目标
- 覆盖B站博主"大佬何金银"最新更新的50期内容
- 从50期内容中整理出前10条被"求出处，求推荐"提及次数最多的故事
- 实现完整的浏览、筛选、跳转功能

## 技术栈

- **前端**: Next.js 14 + React 18 + TypeScript + Tailwind CSS
- **后端**: Node.js + Express
- **爬虫**: Puppeteer + Cheerio
- **数据库**: MySQL 8.0 + Redis + Elasticsearch
- **部署**: Docker + Nginx

## 项目结构

```
buke/
├── docs/                  # 项目文档
├── packages/
│   ├── web/              # 前端应用
│   ├── server/           # 后端服务
│   ├── crawler/          # 爬虫服务
│   └── shared/           # 共享代码
├── docker/               # Docker配置
├── scripts/              # 脚本文件
└── README.md
```

## 快速开始

### 1. 环境准备

- **Node.js**: v18.0.0+
- **pnpm**: v8.0.0+
- **MySQL**: 8.0+
- **Redis**: 7.0+
- **Elasticsearch**: 8.0+

### 2. 安装依赖

```bash
# 安装pnpm（如果未安装）
npm install -g pnpm

# 安装项目依赖
pnpm install
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置数据库连接等信息
```

### 4. 启动服务

#### 开发模式

```bash
# 启动前端开发服务器
cd packages/web
pnpm dev

# 启动后端开发服务器
cd packages/server
pnpm dev

# 启动爬虫服务
cd packages/crawler
pnpm dev
```

#### 生产模式

```bash
# 构建前端
cd packages/web
pnpm build

# 构建后端
cd packages/server
pnpm build

# 构建爬虫
cd packages/crawler
pnpm build

# 启动所有服务
docker-compose up -d
```

## 核心功能

### 前端功能
- 首页展示热门故事TOP10
- 故事列表浏览与筛选
- 故事详情页
- 视频一键直达跳转
- 搜索功能
- 响应式设计

### 后端功能
- 故事管理API
- 视频管理API
- 爬虫调度API
- 搜索API
- 缓存管理

### 爬虫功能
- B站视频列表爬取
- 视频详情爬取
- 评论数据爬取
- 关键词提取与分析
- 热度计算

## 接口文档

### 前端API
- `GET /api/v1/stories` - 获取故事列表
- `GET /api/v1/stories/:id` - 获取故事详情
- `GET /api/v1/stories/hot` - 获取热门故事TOP10
- `GET /api/v1/videos/:bvid` - 获取视频详情
- `GET /api/v1/search` - 搜索故事
- `GET /api/v1/crawler/status` - 爬虫状态
- `POST /api/v1/crawler/trigger` - 触发爬虫任务

## 部署

### Docker部署

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down
```

### 服务器部署

1. 安装Node.js和依赖
2. 构建项目
3. 使用PM2管理进程
4. 配置Nginx反向代理

## 项目状态

- ✅ 项目架构设计
- ✅ 目录结构搭建
- ✅ 前端页面开发
- ✅ 后端API开发
- ✅ 爬虫服务开发
- 📋 依赖安装
- 📋 数据库配置
- 📋 部署上线

## 开发计划

### MVP阶段 (V1)
- [x] 项目初始化
- [x] 架构设计
- [x] 前端页面开发
- [x] 后端API开发
- [x] 爬虫服务开发
- [ ] 数据采集与分析
- [ ] 测试与优化
- [ ] 部署上线

### 后续迭代
- **V1.1**: 增加更多数据源
- **V1.2**: 用户系统与收藏功能
- **V1.3**: 移动端App
- **V2.0**: 社区功能与用户投稿

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
