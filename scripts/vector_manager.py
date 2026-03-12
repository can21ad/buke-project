#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量管理模块 (vector_manager.py)
功能：负责模型加载、向量生成、Chroma入库、增量更新
作者：怖客项目组
版本：1.0.0
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


# 设置HuggingFace镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


class EmbeddingProcessor:
    """
    向量嵌入处理器
    功能：加载模型，将文本转为向量
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化向量化处理器
        
        Args:
            model_name: 嵌入模型名称
        """
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger('VectorDBBuilder.Embedding')
    
    def load_model(self):
        """加载嵌入模型"""
        try:
            self.logger.info(f"正在加载嵌入模型: {self.model_name}")
            
            # 使用镜像加载
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder='./model_cache'
            )
            self.logger.info("✓ 嵌入模型加载成功")
            
        except Exception as e:
            self.logger.error(f"✗ 嵌入模型加载失败: {str(e)}")
            raise
    
    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """将文本列表批量转为向量"""
        if self.model is None:
            raise ValueError("请先调用 load_model() 方法加载模型")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            self.logger.error(f"✗ 向量生成失败: {str(e)}")
            raise
    
    def encode_single(self, text: str) -> Optional[List[float]]:
        """将单个文本转为向量"""
        if self.model is None:
            raise ValueError("请先调用 load_model() 方法加载模型")
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"✗ 单条向量生成失败: {str(e)}")
            return None


class VectorDBManager:
    """
    向量数据库管理器
    功能：管理Chroma数据库，实现增量入库
    """
    
    def __init__(self, db_path: str, collection_name: str):
        """
        初始化向量数据库管理器
        
        Args:
            db_path: 数据库存储路径
            collection_name: 集合名称
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.logger = logging.getLogger('VectorDBBuilder.VectorDB')
    
    def connect(self):
        """连接向量数据库"""
        try:
            # 创建客户端
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合（使用余弦相似度）
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "怖客灵异故事视频向量数据库",
                    "hnsw:space": "cosine"  # 使用余弦相似度，范围0-1
                }
            )
            
            self.logger.info(f"✓ 成功连接到向量数据库: {self.collection_name}")
            self.logger.info(f"  当前数据库已有记录数: {self.collection.count()}")
            
        except Exception as e:
            self.logger.error(f"✗ 向量数据库连接失败: {str(e)}")
            raise
    
    def get_existing_ids(self) -> set:
        """获取当前集合中已有的所有ID"""
        if self.collection is None:
            return set()
        
        try:
            results = self.collection.get()
            existing_ids = set(results.get('ids', []))
            return existing_ids
        except Exception as e:
            self.logger.warning(f"获取已有ID失败: {str(e)}")
            return set()
    
    def add_documents(self, 
                      ids: List[str], 
                      embeddings: List[List[float]], 
                      metadatas: List[Dict[str, Any]],
                      documents: List[str]):
        """添加文档到向量数据库"""
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            self.logger.info(f"✓ 成功添加 {len(ids)} 条记录到向量数据库")
        except Exception as e:
            self.logger.error(f"✗ 添加文档失败: {str(e)}")
            raise
    
    def clear_collection(self):
        """清空集合（用于全量覆盖模式）"""
        try:
            if self.collection is not None:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "怖客灵异故事视频向量数据库",
                        "hnsw:space": "cosine"  # 使用余弦相似度
                    }
                )
                self.logger.info("✓ 集合已清空")
        except Exception as e:
            self.logger.error(f"✗ 清空集合失败: {str(e)}")
            raise
    
    def query(self, 
              query_embedding: List[float], 
              n_results: int = 5,
              where: Optional[Dict] = None) -> Dict:
        """查询相似文档"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["metadatas", "distances", "documents"]
            )
            return results
        except Exception as e:
            self.logger.error(f"✗ 查询失败: {str(e)}")
            return {"ids": [], "metadatas": [], "distances": [], "documents": []}
    
    def get_count(self) -> int:
        """获取集合中的记录数"""
        if self.collection is None:
            return 0
        return self.collection.count()


class VectorManager:
    """
    向量管理器（整合嵌入处理器和数据库管理器）
    功能：批量处理数据并入库
    """
    
    def __init__(self, 
                 db_path: str, 
                 collection_name: str,
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 batch_size: int = 32):
        """
        初始化向量管理器
        
        Args:
            db_path: 向量数据库路径
            collection_name: 集合名称
            model_name: 嵌入模型名称
            batch_size: 批量处理大小
        """
        self.batch_size = batch_size
        self.logger = logging.getLogger('VectorDBBuilder.VectorManager')
        
        # 初始化各模块
        self.embedding_processor = EmbeddingProcessor(model_name)
        self.db_manager = VectorDBManager(db_path, collection_name)
    
    def load_model(self):
        """加载嵌入模型"""
        self.embedding_processor.load_model()
    
    def connect_db(self):
        """连接向量数据库"""
        self.db_manager.connect()
    
    def process_and_add(self, 
                        df, 
                        primary_key_field: str, 
                        embedding_field: str,
                        full_overwrite: bool = False) -> Dict[str, int]:
        """
        批量处理数据并添加到向量数据库
        
        Args:
            df: 清洗后的DataFrame
            primary_key_field: 主键字段名
            embedding_field: 向量生成字段名
            full_overwrite: 是否全量覆盖
            
        Returns:
            统计信息字典
        """
        # 获取已有ID
        existing_ids = self.db_manager.get_existing_ids()
        
        # 统计
        total = len(df)
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        # 错误记录
        error_records = []
        
        # 批量处理
        batch_data = []
        
        self.logger.info(f"开始处理 {total} 条数据...")
        
        # 使用进度条
        pbar = tqdm(total=total, desc="处理进度", unit="条")
        
        for idx, row in df.iterrows():
            try:
                # 获取主键
                primary_key = str(row[primary_key_field])
                
                # 增量模式：检查是否已存在
                if not full_overwrite and primary_key in existing_ids:
                    skip_count += 1
                    pbar.update(1)
                    continue
                
                # 获取向量生成文本
                text = str(row[embedding_field])
                
                # 生成向量
                embedding = self.embedding_processor.encode_single(text)
                
                if embedding is None:
                    fail_count += 1
                    error_records.append({
                        "id": primary_key,
                        "bvid": row.get('bvid', ''),
                        "error": "向量生成失败"
                    })
                    pbar.update(1)
                    continue
                
                # 准备元数据（保留所有字段）
                metadata = {}
                for col in df.columns:
                    value = row[col]
                    # 处理特殊类型
                    if pd.isna(value):
                        metadata[col] = ""
                    elif isinstance(value, (int, float)):
                        metadata[col] = value
                    else:
                        metadata[col] = str(value)
                
                # 添加到批次
                batch_data.append({
                    "id": primary_key,
                    "embedding": embedding,
                    "metadata": metadata,
                    "document": text
                })
                
                # 达到批次大小时批量入库
                if len(batch_data) >= self.batch_size:
                    self._add_batch(batch_data)
                    success_count += len(batch_data)
                    batch_data = []
                
            except Exception as e:
                fail_count += 1
                error_records.append({
                    "id": str(row.get(primary_key_field, '')),
                    "bvid": str(row.get('bvid', '')),
                    "error": str(e)
                })
            
            pbar.update(1)
        
        pbar.close()
        
        # 处理剩余数据
        if batch_data:
            try:
                self._add_batch(batch_data)
                success_count += len(batch_data)
            except Exception as e:
                self.logger.error(f"批次入库失败: {str(e)}")
                fail_count += len(batch_data)
        
        return {
            "success_count": success_count,
            "skip_count": skip_count,
            "fail_count": fail_count,
            "error_records": error_records
        }
    
    def _add_batch(self, batch_data: List[Dict]):
        """批量添加数据到向量数据库"""
        ids = [item["id"] for item in batch_data]
        embeddings = [item["embedding"] for item in batch_data]
        metadatas = [item["metadata"] for item in batch_data]
        documents = [item["document"] for item in batch_data]
        
        self.db_manager.add_documents(ids, embeddings, metadatas, documents)


# 导入pandas
import pandas as pd
