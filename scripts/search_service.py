#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索服务模块 (search_service.py)
功能：负责语义检索、相似推荐、过滤排序
作者：怖客项目组
版本：1.0.0
"""

import logging
from typing import List, Dict, Any, Optional


class SearchService:
    """
    语义搜索服务
    功能：提供交互式的语义检索验证功能
    """
    
    def __init__(self, db_manager, embedding_processor):
        """
        初始化检索服务
        
        Args:
            db_manager: 向量数据库管理器
            embedding_processor: 向量处理器
        """
        self.db_manager = db_manager
        self.embedding_processor = embedding_processor
        self.logger = logging.getLogger('VectorDBBuilder.SearchService')
    
    def search(self, query: str, top_n: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        语义检索
        
        Args:
            query: 查询文本
            top_n: 返回结果数量
            filters: 过滤条件字典，如 {"views": {"$gte": 100000}, "stat2": {"$gte": 1000}}
            
        Returns:
            检索结果列表
        """
        # 将查询文本转为向量
        query_embedding = self.embedding_processor.encode_single(query)
        
        if query_embedding is None:
            self.logger.error("✗ 查询向量化失败")
            return []
        
        # 准备where条件
        where_clause = self._build_where_clause(filters)
        
        # 执行查询
        results = self.db_manager.query(
            query_embedding=query_embedding,
            n_results=top_n * 3,  # 获取更多结果，过滤后可能不够
            where=where_clause
        )
        
        # 格式化结果
        formatted_results = []
        if results.get('ids') and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                # 使用余弦相似度（Chroma已配置为cosine）
                cosine_distance = results['distances'][0][i]
                cosine_similarity = max(0, 1 - cosine_distance)
                
                formatted_results.append({
                    "rank": i + 1,
                    "distance": cosine_distance,
                    "similarity": cosine_similarity,  # 0-1范围，越接近1越相似
                    "id": results['ids'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "document": results['documents'][0][i] if results.get('documents') else ""
                })
        
        return formatted_results
    
    def _build_where_clause(self, filters: Dict = None) -> Optional[Dict]:
        """构建Chroma过滤条件"""
        if not filters:
            return None
        
        where = {}
        for key, value in filters.items():
            if isinstance(value, dict):
                # 处理比较运算符，如 {"$gte": 100000}
                where[key] = value
            else:
                # 精确匹配
                where[key] = value
        
        return where if where else None
    
    def search_with_sort(self, query: str, top_n: int = 5, filters: Dict = None, sort_by: str = None) -> List[Dict[str, Any]]:
        """
        带排序的语义检索
        
        Args:
            query: 查询文本
            top_n: 返回结果数量
            filters: 过滤条件
            sort_by: 排序字段 ("views", "stat2", "date")
            
        Returns:
            检索结果列表
        """
        results = self.search(query, top_n * 2, filters)
        
        if not results:
            return []
        
        # 排序
        if sort_by and results:
            reverse = True  # 默认降序
            if sort_by == "date":
                reverse = False  # 日期升序（最新的排在前面）
            
            # 提取排序值
            def get_sort_key(item):
                metadata = item.get('metadata', {})
                value = metadata.get(sort_by, 0)
                # 处理字符串类型（如 "98.6万"）
                if isinstance(value, str):
                    if '万' in value:
                        try:
                            return float(value.replace('万', '')) * 10000
                        except:
                            return 0
                    elif '万' in value:
                        return 0
                return value
            
            results.sort(key=get_sort_key, reverse=reverse)
        
        return results[:top_n]
    
    def display_results(self, results: List[Dict[str, Any]]):
        """格式化显示检索结果"""
        if not results:
            print("\n未找到相似结果")
            return
        
        print("\n" + "=" * 80)
        print(f"检索到 {len(results)} 条相似内容：")
        print("=" * 80)
        
        for result in results:
            print(f"\n【第{result['rank']}名】相似度: {result['similarity']:.4f}")
            print("-" * 40)
            
            metadata = result.get('metadata', {})
            
            # 显示基本信息
            print(f"主键ID: {result['id']}")
            if metadata.get('bvid'):
                print(f"BV号: {metadata.get('bvid')}")
            if metadata.get('title'):
                print(f"标题: {metadata.get('title')}")
            if metadata.get('views'):
                print(f"浏览量: {metadata.get('views')}")
            if metadata.get('stat2'):
                print(f"评论数: {metadata.get('stat2')}")
            if metadata.get('date'):
                print(f"更新时间: {metadata.get('date')}")
            
            # 显示AI总结摘要
            if metadata.get('summary'):
                summary = metadata.get('summary')
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                print(f"AI总结: {summary}")
            
            print("-" * 40)
        
        print("\n" + "=" * 80)
    
    def interactive_search(self, top_n: int = 5):
        """交互式检索模式"""
        print("\n" + "=" * 80)
        print("欢迎使用语义检索测试功能")
        print("=" * 80)
        print("请输入查询语句，输入 'quit' 或 'exit' 退出")
        print("示例：医院深夜灵异事件、校园宿舍恐怖故事、民间邪术")
        print("=" * 80)
        
        while True:
            try:
                query = input("\n请输入查询语句: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q', '退出']:
                    print("感谢使用，再见！")
                    break
                
                if not query:
                    print("请输入有效的查询语句")
                    continue
                
                # 执行检索
                results = self.search(query, top_n=top_n)
                
                # 显示结果
                self.display_results(results)
                
            except KeyboardInterrupt:
                print("\n\n已退出检索模式")
                break
            except Exception as e:
                print(f"检索出错: {str(e)}")


def search_by_keyword(keyword: str, 
                    db_manager, 
                    embedding_processor, 
                    top_n: int = 5) -> List[Dict[str, Any]]:
    """
    根据关键词检索的便捷函数
    
    Args:
        keyword: 搜索关键词
        db_manager: 向量数据库管理器
        embedding_processor: 向量处理器
        top_n: 返回结果数量
        
    Returns:
        检索结果列表
    """
    service = SearchService(db_manager, embedding_processor)
    return service.search(keyword, top_n)


class SimilarVideoService:
    """
    相似视频推荐服务
    功能：根据BV号获取相似视频推荐
    """
    
    def __init__(self, db_manager):
        """
        初始化相似视频服务
        
        Args:
            db_manager: 向量数据库管理器
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger('VectorDBBuilder.SimilarVideo')
    
    def get_similar_videos(self, bvid: str, top_n: int = 5, exclude_bvid: str = None) -> List[Dict[str, Any]]:
        """
        获取与指定视频相似的视频列表
        
        Args:
            bvid: 视频BV号
            top_n: 返回结果数量
            exclude_bvid: 需要排除的BV号（通常是当前观看的视频）
            
        Returns:
            相似视频列表，每条包含：bvid、title、similarity、views、summary等
        """
        try:
            # 1. 获取指定BV号的向量
            result = self.db_manager.collection.get(
                ids=[bvid],
                include=["embeddings", "metadatas", "documents"]
            )
            
            if not result or not result.get('ids') or len(result['ids']) == 0:
                self.logger.warning(f"未找到BV号: {bvid}")
                return []
            
            # 获取向量 - numpy数组处理
            import numpy as np
            embeddings = result.get('embeddings')
            if embeddings is None or (isinstance(embeddings, np.ndarray) and embeddings.size == 0):
                self.logger.warning(f"BV号 {bvid} 没有存储向量")
                return []
            
            # 转换为list
            if isinstance(embeddings, np.ndarray):
                embedding = embeddings[0].tolist()
            else:
                embedding = embeddings[0]
            
            # 2. 执行相似度检索
            # 需要获取比top_n多1个结果，以便排除当前视频后仍能返回足够数量
            search_n = top_n + 1 if exclude_bvid else top_n
            
            query_results = self.db_manager.query(
                query_embedding=embedding,
                n_results=search_n
            )
            
            # 3. 格式化结果
            similar_videos = []
            if query_results.get('ids') and len(query_results['ids']) > 0:
                for i in range(len(query_results['ids'][0])):
                    result_bvid = query_results['ids'][0][i]
                    
                    # 排除指定BV号
                    if exclude_bvid and result_bvid == exclude_bvid:
                        continue
                    
                    # 排除当前查询的BV号
                    if result_bvid == bvid:
                        continue
                    
                    # 计算相似度
                    cosine_distance = query_results['distances'][0][i]
                    cosine_similarity = max(0, 1 - cosine_distance)
                    
                    metadata = query_results['metadatas'][0][i]
                    
                    similar_videos.append({
                        "bvid": result_bvid,
                        "title": metadata.get('title', ''),
                        "video_url": metadata.get('video_url', f"https://www.bilibili.com/video/{result_bvid}"),
                        "cover_url": metadata.get('cover_url', ''),
                        "views": metadata.get('views', 0),
                        "comment_count": metadata.get('stat2', 0),
                        "duration": metadata.get('duration', ''),
                        "upload_date": metadata.get('date', ''),
                        "summary": metadata.get('summary', ''),
                        "similarity": round(cosine_similarity, 4),  # 0-1范围，越接近1越相似
                        "rank": len(similar_videos) + 1
                    })
                    
                    # 达到所需数量后停止
                    if len(similar_videos) >= top_n:
                        break
            
            self.logger.info(f"为BV号 {bvid} 找到 {len(similar_videos)} 条相似视频")
            return similar_videos
            
        except Exception as e:
            self.logger.error(f"获取相似视频失败: {str(e)}")
            return []
    
    def format_for_api(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        格式化结果为API响应格式
        
        Args:
            videos: 相似视频列表
            
        Returns:
            API响应格式的字典
        """
        if not videos:
            return {
                "code": 404,
                "message": "未找到相似视频",
                "data": []
            }
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": len(videos),
                "videos": videos
            }
        }


def get_similar_videos_by_bvid(bvid: str, 
                                db_manager, 
                                top_n: int = 5, 
                                exclude_bvid: str = None) -> List[Dict[str, Any]]:
    """
    根据BV号获取相似视频的便捷函数
    
    Args:
        bvid: 视频BV号
        db_manager: 向量数据库管理器
        top_n: 返回结果数量
        exclude_bvid: 需要排除的BV号
        
    Returns:
        相似视频列表
    """
    service = SimilarVideoService(db_manager)
    return service.get_similar_videos(bvid, top_n, exclude_bvid)
