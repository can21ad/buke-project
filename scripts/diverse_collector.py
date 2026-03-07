#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - 多样性数据采集脚本
==========================================
采集15个不同视频的评论区数据，确保多样性
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class DiverseDataCollector:
    """多样性数据采集器"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'crawler_data')
        self.output_dir = os.path.join(self.base_dir, 'diverse_data')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        
        self._setup_directories()
        self._setup_logging()
        
        self.cookie = self._load_cookie()
        self.collected_bvids = set()
        self.collection_log = []
    
    def _setup_directories(self):
        """创建必要的目录"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def _setup_logging(self):
        """配置日志系统"""
        log_file = os.path.join(self.logs_dir, f'diverse_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('DiverseCollector')
    
    def _load_cookie(self) -> str:
        """加载Cookie"""
        cookie_file = os.path.join(self.base_dir, 'bilibili_cookies.txt')
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    cookies = []
                    for line in content.split('\n'):
                        if line and not line.startswith('#'):
                            parts = line.split('\t')
                            if len(parts) >= 7:
                                cookies.append(f"{parts[5]}={parts[6]}")
                    return '; '.join(cookies)
            except Exception as e:
                self.logger.warning(f"加载Cookie文件失败: {e}")
        return ""
    
    def _load_all_bvids(self) -> List[str]:
        """加载所有BV号"""
        bvids_file = os.path.join(self.data_dir, 'all_bvids.json')
        if os.path.exists(bvids_file):
            with open(bvids_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('bvid_list', [])
        return []
    
    def _select_diverse_bvids(self, all_bvids: List[str], count: int = 15) -> List[str]:
        """选择多样化的BV号（分散在整个视频列表中）"""
        if len(all_bvids) <= count:
            return all_bvids
        
        # 将BV号分成多个区间，从每个区间随机选择
        # 这样可以确保视频来源的时间多样性
        step = len(all_bvids) // count
        selected = []
        
        for i in range(count):
            start = i * step
            end = min((i + 1) * step, len(all_bvids))
            if start < end:
                # 从每个区间随机选择一个
                bvid = random.choice(all_bvids[start:end])
                selected.append(bvid)
        
        self.logger.info(f"选择了 {len(selected)} 个分散的BV号")
        return selected
    
    def collect_single_video(self, bvid: str) -> Optional[Dict]:
        """采集单个视频的评论数据"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"采集视频: {bvid}")
        self.logger.info(f"{'='*60}")
        
        try:
            sys.path.insert(0, self.base_dir)
            from crawler_v31 import BilibiliCrawlerV31
            
            crawler = BilibiliCrawlerV31(cookie=self.cookie)
            result = crawler.run(bvid)
            
            if result:
                # 保存单独的结果
                output_file = os.path.join(self.output_dir, f'video_{bvid}.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                self.collected_bvids.add(bvid)
                
                record = {
                    'bvid': bvid,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'comment_count': result.get('total_comments', 0),
                    'story_count': len(result.get('past_stories', [])),
                }
                self.collection_log.append(record)
                
                self.logger.info(f"[+] 采集成功: {result.get('total_comments', 0)} 条评论")
                return result
        
        except Exception as e:
            self.logger.error(f"[-] 采集失败: {e}")
            self.collection_log.append({
                'bvid': bvid,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
        
        return None
    
    def run_collection(self, total_videos: int = 15, 
                       batch_size: int = 3,
                       batch_interval: int = 60) -> Dict:
        """
        执行多样性数据采集
        
        Args:
            total_videos: 总共采集视频数
            batch_size: 每批采集数量
            batch_interval: 批次间隔时间(秒)
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("怖客 - 多样性数据采集")
        self.logger.info(f"目标: {total_videos} 个视频, 每批 {batch_size} 个")
        self.logger.info("="*60)
        
        start_time = time.time()
        
        # 加载所有BV号
        all_bvids = self._load_all_bvids()
        if not all_bvids:
            self.logger.error("[-] 没有可用的BV号，请先运行BV爬虫")
            return {'success': False, 'error': 'No BV IDs available'}
        
        # 选择多样化的BV号
        selected_bvids = self._select_diverse_bvids(all_bvids, total_videos)
        
        self.logger.info(f"\n选中的BV号 (分散在整个视频列表中):")
        for i, bvid in enumerate(selected_bvids, 1):
            self.logger.info(f"  {i}. {bvid}")
        
        # 分批采集
        all_results = []
        batches = [selected_bvids[i:i+batch_size] for i in range(0, len(selected_bvids), batch_size)]
        
        for batch_idx, batch in enumerate(batches, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"批次 {batch_idx}/{len(batches)}")
            self.logger.info(f"{'='*60}")
            
            for bvid in batch:
                result = self.collect_single_video(bvid)
                if result:
                    all_results.append(result)
                time.sleep(3)  # 视频间隔
            
            if batch_idx < len(batches):
                self.logger.info(f"\n等待 {batch_interval} 秒后继续下一批...")
                time.sleep(batch_interval)
        
        # 合并所有结果
        merged_result = {
            'generated_at': datetime.now().isoformat(),
            'total_videos': len(all_results),
            'total_comments': sum(r.get('total_comments', 0) for r in all_results),
            'videos': all_results,
            'collection_log': self.collection_log,
        }
        
        merged_file = os.path.join(self.output_dir, 'diverse_collection_merged.json')
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_result, f, ensure_ascii=False, indent=2)
        
        # 保存采集日志
        log_file = os.path.join(self.output_dir, 'collection_log.json')
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.collection_log, f, ensure_ascii=False, indent=2)
        
        duration = time.time() - start_time
        
        self.logger.info("\n" + "="*60)
        self.logger.info("采集完成摘要")
        self.logger.info("="*60)
        self.logger.info(f"总耗时: {duration:.2f} 秒")
        self.logger.info(f"成功采集: {len(all_results)} 个视频")
        self.logger.info(f"总评论数: {merged_result['total_comments']}")
        self.logger.info(f"数据保存至: {self.output_dir}")
        
        return merged_result


def main():
    """主函数"""
    collector = DiverseDataCollector()
    
    result = collector.run_collection(
        total_videos=15,
        batch_size=3,
        batch_interval=30
    )
    
    print(f"\n[+] 采集完成，共 {result.get('total_videos', 0)} 个视频")


if __name__ == "__main__":
    main()
