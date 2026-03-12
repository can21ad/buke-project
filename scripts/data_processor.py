#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理模块 (data_processor.py)
功能：负责CSV读取、数据校验、去重、过滤
作者：怖客项目组
版本：1.0.0
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pandas as pd


class CSVReader:
    """
    CSV数据读取器
    功能：读取CSV文件，自动识别编码，处理数据去重和过滤
    """
    
    def __init__(self, file_path: str):
        """
        初始化CSV读取器
        
        Args:
            file_path: CSV文件路径
        """
        self.file_path = file_path
        self.encoding_list = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-8-sig']
        self.df = None
        self.logger = logging.getLogger('VectorDBBuilder.DataProcessor')
    
    def detect_encoding(self) -> str:
        """自动检测CSV文件编码"""
        for encoding in self.encoding_list:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    f.read(1024)
                self.logger.info(f"✓ 检测到CSV文件编码: {encoding}")
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        self.logger.warning("⚠ 无法自动检测编码，使用默认编码 utf-8")
        return 'utf-8'
    
    def read_csv(self) -> pd.DataFrame:
        """读取CSV文件"""
        encoding = self.detect_encoding()
        
        try:
            self.df = pd.read_csv(self.file_path, encoding=encoding)
            self.logger.info(f"✓ CSV文件读取成功，共 {len(self.df)} 条记录")
            self.logger.info(f"  CSV字段列表: {list(self.df.columns)}")
            return self.df
        except Exception as e:
            self.logger.error(f"✗ CSV文件读取失败: {str(e)}")
            raise
    
    def validate_required_fields(self, required_fields: List[str]) -> bool:
        """验证必填字段是否存在"""
        if self.df is None:
            self.logger.error("✗ 请先调用 read_csv() 方法读取数据")
            return False
        
        missing_fields = []
        for field in required_fields:
            if field not in self.df.columns:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.error(f"✗ CSV缺少必填字段: {missing_fields}")
            self.logger.error(f"  当前CSV字段: {list(self.df.columns)}")
            return False
        
        self.logger.info("✓ 必填字段验证通过")
        return True
    
    def clean_data(self, primary_key_field: str, embedding_field: str) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        数据清洗：去重、过滤无效数据
        
        Args:
            primary_key_field: 主键字段名
            embedding_field: 向量生成字段名
            
        Returns:
            清洗后的DataFrame和统计信息
        """
        if self.df is None:
            raise ValueError("请先调用 read_csv() 方法读取数据")
        
        stats = {
            "total": len(self.df),
            "duplicate_removed": 0,
            "invalid_filtered": 0,
            "valid": 0
        }
        
        original_count = len(self.df)
        
        # 1. 去除主键为空的记录
        self.df = self.df.dropna(subset=[primary_key_field])
        self.df[primary_key_field] = self.df[primary_key_field].astype(str)
        
        # 2. 去除向量字段为空的记录
        self.df = self.df.dropna(subset=[embedding_field])
        
        # 3. 去除向量字段为空字符串的记录
        self.df = self.df[self.df[embedding_field].str.strip() != ""]
        
        stats["invalid_filtered"] = original_count - len(self.df)
        
        # 4. 按主键去重，保留第一条
        self.df = self.df.drop_duplicates(subset=[primary_key_field], keep='first')
        
        stats["duplicate_removed"] = original_count - stats["invalid_filtered"] - len(self.df)
        stats["valid"] = len(self.df)
        
        self.logger.info("✓ 数据清洗完成")
        self.logger.info(f"  总记录数: {stats['total']}")
        self.logger.info(f"  去除重复: {stats['duplicate_removed']}")
        self.logger.info(f"  过滤无效: {stats['invalid_filtered']}")
        self.logger.info(f"  有效数据: {stats['valid']}")
        
        return self.df, stats
    
    def check_bvid_duplicates(self, bvid_field: str = "bvid") -> List[str]:
        """检查BV号是否重复"""
        if self.df is None:
            return []
        
        if bvid_field not in self.df.columns:
            return []
        
        self.df[bvid_field] = self.df[bvid_field].astype(str)
        duplicates = self.df[self.df.duplicated(subset=[bvid_field], keep=False)]
        duplicate_bvids = duplicates[bvid_field].unique().tolist()
        
        if duplicate_bvids:
            self.logger.warning(f"⚠ 发现 {len(duplicate_bvids)} 个重复的BV号，将保留第一条记录")
            for bvid in duplicate_bvids[:5]:
                self.logger.warning(f"  重复BV号: {bvid}")
        
        return duplicate_bvids


def process_csv(csv_path: str, primary_key_field: str, embedding_field: str) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    处理CSV文件的便捷函数
    
    Args:
        csv_path: CSV文件路径
        primary_key_field: 主键字段名
        embedding_field: 向量生成字段名
        
    Returns:
        清洗后的DataFrame和统计信息
    """
    reader = CSVReader(csv_path)
    df = reader.read_csv()
    reader.validate_required_fields([primary_key_field, embedding_field])
    reader.check_bvid_duplicates()
    return reader.clean_data(primary_key_field, embedding_field)
