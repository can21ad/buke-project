#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客向量数据库构建工具 - 主程序
功能：整合数据处理、向量管理、搜索服务模块
作者：怖客项目组
版本：1.1.0

使用方法：
    python vector_db_builder.py

依赖安装：
    pip install pandas chromadb sentence-transformers tqdm numpy
"""

# ============================================
# 配置项（请根据实际情况修改）
# ============================================

# CSV文件路径（必填，请修改为您的CSV文件实际路径）
CSV_FILE_PATH = "d:/怖客/scripts/space_merged_with_summary.csv"

# Chroma数据库存储路径
CHROMA_DB_PATH = "./chroma_db"

# 向量集合名称
COLLECTION_NAME = "ghost_story_video_collection"

# 嵌入模型配置
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# 批量处理大小
BATCH_SIZE = 32

# 是否启用全量覆盖模式（默认False，使用增量模式）
FULL_OVERWRITE_MODE = False

# 检索返回结果数量
RETRIEVE_TOP_N = 5

# 主键字段名
PRIMARY_KEY_FIELD = "bvid"

# 向量生成字段名
EMBEDDING_TEXT_FIELD = "summary"

# ============================================
# 导入模块
# ============================================

import os
import sys
import json
import logging
from datetime import datetime

# 设置HuggingFace镜像（必须在导入sentence_transformers之前）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 导入自定义模块
from data_processor import CSVReader
from vector_manager import VectorManager
from search_service import SearchService

# ============================================
# 日志配置
# ============================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

ERROR_LOG_FILE = os.path.join(LOG_DIR, f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")


def setup_logging():
    """配置日志系统"""
    logger = logging.getLogger('VectorDBBuilder')
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# ============================================
# 主程序
# ============================================

def main():
    """主函数"""
    logger = setup_logging()
    
    print("\n" + "=" * 60)
    print("  怖客灵异故事视频向量数据库构建工具")
    print("  版本: 1.1.0 (模块化)")
    print("=" * 60)
    
    # 检查CSV文件是否存在
    if not os.path.exists(CSV_FILE_PATH):
        logger.error(f"✗ CSV文件不存在: {CSV_FILE_PATH}")
        logger.error("请修改脚本开头的 CSV_FILE_PATH 配置项")
        sys.exit(1)
    
    try:
        # ========== 步骤1: 读取CSV数据 ==========
        logger.info("\n[步骤1/4] 读取CSV数据...")
        csv_reader = CSVReader(CSV_FILE_PATH)
        df = csv_reader.read_csv()
        
        # 验证必填字段
        if not csv_reader.validate_required_fields([PRIMARY_KEY_FIELD, EMBEDDING_TEXT_FIELD]):
            raise ValueError("CSV缺少必填字段")
        
        # 检查BV号重复
        csv_reader.check_bvid_duplicates()
        
        # ========== 步骤2: 数据清洗 ==========
        logger.info("\n[步骤2/4] 数据清洗...")
        df, clean_stats = csv_reader.clean_data(PRIMARY_KEY_FIELD, EMBEDDING_TEXT_FIELD)
        
        # ========== 步骤3: 向量入库 ==========
        logger.info("\n[步骤3/4] 向量处理与入库...")
        
        # 初始化向量管理器
        vector_manager = VectorManager(
            db_path=CHROMA_DB_PATH,
            collection_name=COLLECTION_NAME,
            model_name=EMBEDDING_MODEL_NAME,
            batch_size=BATCH_SIZE
        )
        
        # 加载模型
        vector_manager.load_model()
        
        # 连接数据库
        vector_manager.connect_db()
        
        # 全量覆盖模式
        if FULL_OVERWRITE_MODE:
            logger.info("⚠ 启用全量覆盖模式，将清空原有数据")
            vector_manager.db_manager.clear_collection()
        
        # 增量入库
        stats = vector_manager.process_and_add(
            df=df,
            primary_key_field=PRIMARY_KEY_FIELD,
            embedding_field=EMBEDDING_TEXT_FIELD,
            full_overwrite=FULL_OVERWRITE_MODE
        )
        
        # ========== 步骤4: 输出统计 ==========
        logger.info("\n" + "=" * 60)
        logger.info("处理统计报表")
        logger.info("=" * 60)
        logger.info(f"CSV总数据条数:     {clean_stats['total']}")
        logger.info(f"有效数据条数:     {clean_stats['valid']}")
        logger.info(f"成功入库条数:     {stats['success_count']}")
        logger.info(f"跳过重复条数:     {stats['skip_count']}")
        logger.info(f"处理失败条数:     {stats['fail_count']}")
        
        if clean_stats['valid'] > 0:
            success_rate = (stats['success_count'] / clean_stats['valid']) * 100
            logger.info(f"入库成功率:       {success_rate:.2f}%")
        
        logger.info("=" * 60)
        
        # 保存错误记录
        if stats['error_records']:
            error_file = os.path.join(LOG_DIR, f"failed_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(stats['error_records'], f, ensure_ascii=False, indent=2)
            logger.warning(f"⚠ 有 {len(stats['error_records'])} 条记录处理失败，已记录到: {error_file}")
        
        logger.info("\n✓ 向量数据库构建完成！")
        
        # ========== 步骤5: 检索测试 ==========
        print("\n" + "=" * 60)
        print("是否需要进行语义检索测试？")
        print("=" * 60)
        print("输入 'y' 或 'yes' 开始检索测试")
        print("输入其他内容跳过")
        print("=" * 60)
        
        choice = input("\n请输入选项: ").strip().lower()
        
        if choice in ['y', 'yes', '是']:
            # 创建搜索服务
            search_service = SearchService(
                db_manager=vector_manager.db_manager,
                embedding_processor=vector_manager.embedding_processor
            )
            # 启动交互式检索
            search_service.interactive_search(top_n=RETRIEVE_TOP_N)
        else:
            print("\n已跳过检索测试，构建完成！")
        
    except KeyboardInterrupt:
        logger.info("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n✗ 程序异常退出: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
