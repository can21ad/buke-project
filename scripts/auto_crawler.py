#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - 自动化爬虫执行脚本
==========================================
非交互式执行，支持命令行参数
"""

import os
import sys
import json
import time
import logging
import traceback
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BukeAutoCrawler:
    """怖客自动化爬虫"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'crawler_data')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        
        self._setup_directories()
        self._setup_logging()
        
        self.cookie = self._load_cookie()
        self.status = self._load_status()
    
    def _setup_directories(self):
        """创建必要的目录"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def _setup_logging(self):
        """配置日志系统"""
        log_file = os.path.join(self.logs_dir, f'auto_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('BukeAutoCrawler')
    
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
    
    def _load_status(self) -> Dict:
        """加载执行状态"""
        status_file = os.path.join(self.data_dir, 'auto_status.json')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'last_run': None,
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'crawlers': {
                'bv_crawler': {'runs': 0, 'success': 0, 'failed': 0, 'last_run': None, 'last_count': 0},
                'video_crawler': {'runs': 0, 'success': 0, 'failed': 0, 'last_run': None, 'last_count': 0},
                'comment_crawler': {'runs': 0, 'success': 0, 'failed': 0, 'last_run': None, 'last_count': 0},
            }
        }
    
    def _save_status(self):
        """保存执行状态"""
        status_file = os.path.join(self.data_dir, 'auto_status.json')
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, ensure_ascii=False, indent=2)
    
    def _record_execution(self, crawler_name: str, success: bool, 
                          duration: float, data_count: int = 0, error: str = None):
        """记录执行结果"""
        self.status['crawlers'][crawler_name]['runs'] += 1
        self.status['crawlers'][crawler_name]['last_run'] = datetime.now().isoformat()
        self.status['crawlers'][crawler_name]['last_count'] = data_count
        
        if success:
            self.status['crawlers'][crawler_name]['success'] += 1
        else:
            self.status['crawlers'][crawler_name]['failed'] += 1
        
        self._save_status()
    
    def run_bv_crawler(self, mid: str = '28346875', max_videos: int = 500) -> Dict:
        """执行BV号爬虫"""
        self.logger.info("="*60)
        self.logger.info("[1/3] BV号爬虫 - 开始执行")
        self.logger.info("="*60)
        
        start_time = time.time()
        result = {'success': False, 'bvids': [], 'count': 0, 'duration': 0}
        
        try:
            sys.path.insert(0, self.base_dir)
            from ytdlp_crawler import YtdlpBilibiliCrawler
            
            crawler = YtdlpBilibiliCrawler(cookie=self.cookie)
            videos = crawler.get_all_bvids(mid, max_videos)
            
            if videos:
                output_file = os.path.join(self.data_dir, 'all_bvids.json')
                crawler.save_bvids(videos, output_file)
                
                result['success'] = True
                result['bvids'] = [v['bvid'] for v in videos]
                result['count'] = len(videos)
                
                self.logger.info(f"[+] BV号爬虫完成: {result['count']} 个视频")
            else:
                self.logger.warning("[!] BV号爬虫未获取到数据")
        
        except Exception as e:
            self.logger.error(f"[-] BV号爬虫失败: {e}")
            self.logger.debug(traceback.format_exc())
            result['error'] = str(e)
        
        result['duration'] = time.time() - start_time
        self._record_execution('bv_crawler', result['success'], result['duration'], result['count'])
        
        return result
    
    def run_video_crawler(self, bvids: list = None, max_videos: int = 10) -> Dict:
        """执行视频信息爬虫"""
        self.logger.info("="*60)
        self.logger.info("[2/3] 视频信息爬虫 - 开始执行")
        self.logger.info("="*60)
        
        start_time = time.time()
        result = {'success': False, 'videos': [], 'count': 0, 'duration': 0}
        
        try:
            sys.path.insert(0, self.base_dir)
            from ytdlp_crawler import YtdlpBilibiliCrawler
            
            if not bvids:
                bvids_file = os.path.join(self.data_dir, 'all_bvids.json')
                if os.path.exists(bvids_file):
                    with open(bvids_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        bvids = data.get('bvid_list', [])[:max_videos]
            
            if not bvids:
                self.logger.warning("[!] 没有可用的BV号")
                return result
            
            crawler = YtdlpBilibiliCrawler(cookie=self.cookie)
            videos = crawler.batch_get_info(bvids[:max_videos], 
                                            os.path.join(self.data_dir, 'video_details.json'))
            
            if videos:
                result['success'] = True
                result['videos'] = videos
                result['count'] = len(videos)
                
                self.logger.info(f"[+] 视频信息爬虫完成: {result['count']} 个视频详情")
        
        except Exception as e:
            self.logger.error(f"[-] 视频信息爬虫失败: {e}")
            self.logger.debug(traceback.format_exc())
            result['error'] = str(e)
        
        result['duration'] = time.time() - start_time
        self._record_execution('video_crawler', result['success'], result['duration'], result['count'])
        
        return result
    
    def run_comment_crawler(self, bvids: list = None, max_videos: int = 3) -> Dict:
        """执行评论区爬虫"""
        self.logger.info("="*60)
        self.logger.info("[3/3] 评论区爬虫 - 开始执行")
        self.logger.info("="*60)
        
        start_time = time.time()
        result = {'success': False, 'stories': [], 'count': 0, 'duration': 0}
        
        try:
            sys.path.insert(0, self.base_dir)
            from crawler_v31 import BilibiliCrawlerV31
            
            if not bvids:
                bvids_file = os.path.join(self.data_dir, 'all_bvids.json')
                if os.path.exists(bvids_file):
                    with open(bvids_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        bvids = data.get('bvid_list', [])[:max_videos]
            
            if not bvids:
                self.logger.warning("[!] 没有可用的BV号")
                return result
            
            crawler = BilibiliCrawlerV31(cookie=self.cookie)
            
            all_results = []
            for i, bvid in enumerate(bvids[:max_videos], 1):
                self.logger.info(f"\n[{i}/{min(len(bvids), max_videos)}] 处理视频: {bvid}")
                
                try:
                    video_result = crawler.run(bvid)
                    if video_result:
                        all_results.append(video_result)
                        
                        output_file = os.path.join(self.data_dir, f'crawler_result_{bvid}.json')
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(video_result, f, ensure_ascii=False, indent=2)
                    
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"处理视频 {bvid} 失败: {e}")
                    continue
            
            if all_results:
                merged_result = {
                    'generated_at': datetime.now().isoformat(),
                    'total_videos': len(all_results),
                    'results': all_results
                }
                
                merged_file = os.path.join(self.data_dir, 'buke_crawler_merged.json')
                with open(merged_file, 'w', encoding='utf-8') as f:
                    json.dump(merged_result, f, ensure_ascii=False, indent=2)
                
                total_stories = sum(len(r.get('past_stories', [])) for r in all_results)
                
                result['success'] = True
                result['stories'] = all_results
                result['count'] = total_stories
                
                self.logger.info(f"[+] 评论区爬虫完成: {total_stories} 个故事")
        
        except Exception as e:
            self.logger.error(f"[-] 评论区爬虫失败: {e}")
            self.logger.debug(traceback.format_exc())
            result['error'] = str(e)
        
        result['duration'] = time.time() - start_time
        self._record_execution('comment_crawler', result['success'], result['duration'], result['count'])
        
        return result
    
    def run_full_pipeline(self, mid: str = '28346875',
                          max_bvids: int = 500,
                          max_video_details: int = 10,
                          max_comment_videos: int = 3,
                          interval: int = 5) -> Dict:
        """执行完整流程"""
        self.logger.info("\n" + "="*60)
        self.logger.info("怖客爬虫系统 - 自动执行")
        self.logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*60)
        
        pipeline_start = time.time()
        pipeline_result = {
            'start_time': datetime.now().isoformat(),
            'success': False,
            'stages': {},
            'total_duration': 0,
            'errors': []
        }
        
        self.status['total_runs'] += 1
        
        try:
            # 阶段1: BV号爬虫
            bv_result = self.run_bv_crawler(mid, max_bvids)
            pipeline_result['stages']['bv_crawler'] = bv_result
            
            if not bv_result['success']:
                pipeline_result['errors'].append("BV号爬虫失败")
            
            time.sleep(interval)
            
            # 阶段2: 视频信息爬虫
            video_result = self.run_video_crawler(
                bvids=bv_result.get('bvids', []),
                max_videos=max_video_details
            )
            pipeline_result['stages']['video_crawler'] = video_result
            
            if not video_result['success']:
                pipeline_result['errors'].append("视频信息爬虫失败")
            
            time.sleep(interval)
            
            # 阶段3: 评论区爬虫
            comment_result = self.run_comment_crawler(
                bvids=bv_result.get('bvids', []),
                max_videos=max_comment_videos
            )
            pipeline_result['stages']['comment_crawler'] = comment_result
            
            if not comment_result['success']:
                pipeline_result['errors'].append("评论区爬虫失败")
            
            # 判断整体成功
            pipeline_result['success'] = any([
                bv_result['success'],
                video_result['success'],
                comment_result['success']
            ])
            
            if pipeline_result['success']:
                self.status['successful_runs'] += 1
            else:
                self.status['failed_runs'] += 1
        
        except Exception as e:
            self.logger.error(f"[-] 管道执行异常: {e}")
            pipeline_result['errors'].append(str(e))
            self.status['failed_runs'] += 1
        
        pipeline_result['total_duration'] = time.time() - pipeline_start
        pipeline_result['end_time'] = datetime.now().isoformat()
        
        self.status['last_run'] = pipeline_result['end_time']
        self._save_status()
        
        self._print_summary(pipeline_result)
        
        return pipeline_result
    
    def _print_summary(self, result: Dict):
        """打印执行摘要"""
        self.logger.info("\n" + "="*60)
        self.logger.info("执行摘要")
        self.logger.info("="*60)
        
        self.logger.info(f"状态: {'成功' if result['success'] else '失败'}")
        self.logger.info(f"总耗时: {result['total_duration']:.2f} 秒")
        
        self.logger.info("\n各阶段执行情况:")
        for name, stage in result['stages'].items():
            status = "✓" if stage.get('success') else "✗"
            duration = stage.get('duration', 0)
            count = stage.get('count', 0)
            self.logger.info(f"  {status} {name}: {duration:.2f}秒, 数据量: {count}")
        
        if result.get('errors'):
            self.logger.info("\n错误信息:")
            for err in result['errors']:
                self.logger.info(f"  - {err}")
        
        self.logger.info("\n累计执行统计:")
        self.logger.info(f"  总运行: {self.status['total_runs']} 次")
        self.logger.info(f"  成功: {self.status['successful_runs']} 次")
        self.logger.info(f"  失败: {self.status['failed_runs']} 次")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='怖客爬虫系统 - 自动化执行')
    parser.add_argument('--mid', type=str, default='28346875', help='UP主ID')
    parser.add_argument('--max-bvids', type=int, default=500, help='最大BV号数量')
    parser.add_argument('--max-videos', type=int, default=10, help='最大视频详情数量')
    parser.add_argument('--max-comments', type=int, default=3, help='最大评论爬取视频数')
    parser.add_argument('--interval', type=int, default=5, help='爬虫间隔时间(秒)')
    parser.add_argument('--loop', action='store_true', help='循环执行模式')
    parser.add_argument('--loop-interval', type=int, default=60, help='循环间隔(分钟)')
    parser.add_argument('--max-loops', type=int, default=None, help='最大循环次数')
    
    args = parser.parse_args()
    
    crawler = BukeAutoCrawler()
    
    if args.loop:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"第 {iteration} 次执行")
            print(f"{'='*60}")
            
            crawler.run_full_pipeline(
                mid=args.mid,
                max_bvids=args.max_bvids,
                max_video_details=args.max_videos,
                max_comment_videos=args.max_comments,
                interval=args.interval
            )
            
            if args.max_loops and iteration >= args.max_loops:
                break
            
            print(f"\n下次执行: {args.loop_interval} 分钟后")
            time.sleep(args.loop_interval * 60)
    else:
        crawler.run_full_pipeline(
            mid=args.mid,
            max_bvids=args.max_bvids,
            max_video_details=args.max_videos,
            max_comment_videos=args.max_comments,
            interval=args.interval
        )


if __name__ == "__main__":
    main()
