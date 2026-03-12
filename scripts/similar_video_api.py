#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相似视频推荐API服务
功能：提供HTTP API用于相似视频推荐
作者：怖客项目组
版本：1.0.0

运行方式：
    python similar_video_api.py

API端点：
    GET /api/similar?bvid=BV号&top_n=5
"""

import os
import sys
from typing import Optional

# 设置HuggingFace镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 导入向量管理模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vector_manager import VectorManager, EmbeddingProcessor
from search_service import SimilarVideoService

# FastAPI
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ============================================
# 配置项
# ============================================

# Chroma数据库路径
CHROMA_DB_PATH = "./chroma_db"

# 向量集合名称
COLLECTION_NAME = "ghost_story_video_collection"

# 嵌入模型名称
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# API配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# ============================================
# 初始化服务
# ============================================

print("正在初始化向量数据库服务...")

# 初始化向量管理器
vector_manager = VectorManager(
    db_path=CHROMA_DB_PATH,
    collection_name=COLLECTION_NAME,
    model_name=EMBEDDING_MODEL_NAME,
    batch_size=32
)

# 连接数据库
vector_manager.connect_db()

# 加载模型
vector_manager.load_model()

# 创建相似视频服务
similar_video_service = SimilarVideoService(vector_manager.db_manager)

print("✓ 向量数据库服务初始化完成")

# ============================================
# 创建FastAPI应用
# ============================================

app = FastAPI(
    title="怖客相似视频推荐API",
    description="基于向量数据库的相似视频推荐服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "怖客相似视频推荐API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


@app.get("/api/similar")
async def get_similar_videos(
    bvid: str = Query(..., description="视频BV号", example="BV1xxx"),
    top_n: int = Query(5, description="返回结果数量", ge=1, le=20)
):
    """
    获取相似视频推荐
    
    Args:
        bvid: 视频BV号
        top_n: 返回结果数量
        
    Returns:
        相似视频列表
    """
    if not bvid:
        raise HTTPException(status_code=400, detail="缺少bvid参数")
    
    try:
        # 获取相似视频
        videos = similar_video_service.get_similar_videos(
            bvid=bvid,
            top_n=top_n
        )
        
        # 格式化返回
        return similar_video_service.format_for_api(videos)
        
    except Exception as e:
        print(f"获取相似视频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.get("/api/search")
async def search_videos(
    keyword: str = Query(..., description="搜索关键词", example="医院灵异事件"),
    top_n: int = Query(10, description="返回结果数量", ge=1, le=50),
    sort_by: str = Query(None, description="排序字段: views(浏览量), stat2(评论数), date(最新)"),
    min_views: int = Query(None, description="最小浏览量"),
    min_comments: int = Query(None, description="最小评论数"),
    max_duration: int = Query(None, description="最大时长(分钟)")
):
    """
    语义搜索视频
    
    Args:
        keyword: 搜索关键词
        top_n: 返回结果数量
        sort_by: 排序字段 (views, stat2, date)
        min_views: 最小浏览量
        min_comments: 最小评论数
        max_duration: 最大时长(分钟)
        
    Returns:
        搜索结果列表
    """
    if not keyword:
        raise HTTPException(status_code=400, detail="缺少keyword参数")
    
    try:
        # 搜索视频 - 不过滤，在结果中处理
        from search_service import SearchService
        search_service = SearchService(vector_manager.db_manager, vector_manager.embedding_processor)
        
        # 获取足够多的结果用于过滤和排序
        results = search_service.search(keyword, top_n * 3, None)
        
        if not results:
            return {"code": 404, "message": "未找到相关视频", "data": []}
        
        # 在Python端过滤和排序
        filtered_results = []
        for r in results:
            metadata = r.get('metadata', {})
            
            # 浏览量过滤
            if min_views:
                views_val = parse_views(metadata.get('views', 0))
                if views_val < min_views:
                    continue
            
            # 评论数过滤
            if min_comments:
                stat2_val = metadata.get('stat2', 0)
                if isinstance(stat2_val, str):
                    comment_val = parse_views(stat2_val)
                else:
                    comment_val = int(stat2_val) if stat2_val else 0
                if comment_val < min_comments:
                    continue
            
            # 时长过滤
            if max_duration:
                duration_str = metadata.get('duration', '')
                duration_minutes = parse_duration(duration_str)
                if duration_minutes and duration_minutes > max_duration:
                    continue
            
            filtered_results.append(r)
        
        # 排序
        if sort_by and filtered_results:
            reverse = True
            if sort_by == "date":
                reverse = True  # 日期最新的排在前面
            
            def get_sort_key(item):
                metadata = item.get('metadata', {})
                value = metadata.get(sort_by, 0)
                
                # 日期字段特殊处理
                if sort_by == "date":
                    date_str = metadata.get('date', '')
                    if date_str:
                        try:
                            # 解析日期格式如 "2022/8/26"
                            parts = date_str.split('/')
                            if len(parts) == 3:
                                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                                return year * 10000 + month * 100 + day
                        except:
                            pass
                    return 0
                
                # 数字字段使用parse_views处理（支持"万"单位）
                if isinstance(value, str):
                    return parse_views(value)
                try:
                    return int(value) if value else 0
                except:
                    return 0
            
            filtered_results.sort(key=get_sort_key, reverse=reverse)
        
        results = filtered_results[:top_n]
        
        # 格式化返回
        videos = []
        for r in results:
            metadata = r.get('metadata', {})
            
            # 时长过滤（需要在结果中过滤）
            if max_duration:
                duration_str = metadata.get('duration', '')
                duration_minutes = parse_duration(duration_str)
                if duration_minutes and duration_minutes > max_duration:
                    continue
            
            videos.append({
                "bvid": r['id'],
                "title": metadata.get('title', ''),
                "video_url": metadata.get('video_url', f"https://www.bilibili.com/video/{r['id']}"),
                "cover_url": metadata.get('cover_url', ''),
                "cover_local": metadata.get('local_cover', ''),
                "views": parse_views(metadata.get('views', 0)),
                "play_count": parse_views(metadata.get('views', 0)),
                "comment_count": parse_views(metadata.get('stat2', 0)),
                "duration": metadata.get('duration', ''),
                "duration_str": metadata.get('duration', ''),
                "upload_date": metadata.get('date', ''),
                "date": metadata.get('date', ''),
                "summary": metadata.get('summary', ''),
                "episode": 0,
                "part": "",
                "similarity": r.get('similarity', 0)
            })
        
        if not videos:
            return {"code": 404, "message": "未找到相关视频", "data": []}
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": len(videos),
                "videos": videos
            }
        }
        
    except Exception as e:
        print(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


def parse_duration(duration_str: str) -> int:
    """解析时长字符串为分钟数"""
    if not duration_str:
        return 0
    try:
        # 处理格式如 "1:03:54" 或 "39:49:00" 或 "05:30"
        parts = duration_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        elif len(parts) == 2:
            return int(parts[0])
    except:
        pass
    return 0


def parse_views(views_str):
    """解析浏览量字符串为数字，支持'万'单位"""
    if not views_str:
        return 0
    try:
        views_str = str(views_str).strip()
        if not views_str:
            return 0
        # 处理包含'万'的情况，如'1.3万'
        if '万' in views_str:
            num_part = views_str.replace('万', '').strip()
            return int(float(num_part) * 10000)
        # 处理纯数字字符串
        return int(float(views_str))
    except Exception as e:
        print(f"[parse_views] 解析失败: {views_str}, 错误: {e}")
        return 0


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("  怖客相似视频推荐API服务")
    print(f"  版本: 1.0.0")
    print(f"{'='*60}")
    print(f"API地址: http://localhost:{API_PORT}")
    print(f"文档地址: http://localhost:{API_PORT}/docs")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
