#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - 爬虫系统主控程序
==========================================
整合三个爬虫程序，实现自动化循环执行
1. BV号爬虫 - 获取UP主所有视频BV号
2. 视频信息爬虫 - 获取视频详细信息
3. 评论区爬虫 - 分析评论提取热门故事
"""

import os
import sys
import json
import time
import logging
import traceback
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class CrawlerOrchestrator:
    """爬虫编排器 - 统一管理三个爬虫的执行"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = self.base_dir
        self.data_dir = os.path.join(self.base_dir, 'crawler_data')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        
        self._setup_directories()
        self._setup_logging()
        
        self.cookie = self._load_cookie()
        self.status = self._load_status()
        
        self.execution_log = []
    
    def _setup_directories(self):
        """创建必要的目录"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def _setup_logging(self):
        """配置日志系统"""
        log_file = os.path.join(self.logs_dir, f'crawler_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('BukeCrawler')
    
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
        status_file = os.path.join(self.data_dir, 'crawler_status.json')
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
                'bv_crawler': {'runs': 0, 'success': 0, 'failed': 0, 'last_run': None},
                'video_crawler': {'runs': 0, 'success': 0, 'failed': 0, 'last_run': None},
                'comment_crawler': {'runs': 0, 'success': 0, 'failed': 0, 'last_run': None},
            },
            'data_stats': {
                'total_bvids': 0,
                'total_videos': 0,
                'total_stories': 0,
            }
        }
    
    def _save_status(self):
        """保存执行状态"""
        status_file = os.path.join(self.data_dir, 'crawler_status.json')
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, ensure_ascii=False, indent=2)
    
    def _record_execution(self, crawler_name: str, success: bool, 
                          duration: float, data_count: int = 0, error: str = None):
        """记录执行日志"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'crawler': crawler_name,
            'success': success,
            'duration_seconds': round(duration, 2),
            'data_count': data_count,
            'error': error
        }
        
        self.execution_log.append(record)
        
        log_file = os.path.join(self.logs_dir, 'execution_log.json')
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                pass
        
        logs.append(record)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs[-1000:], f, ensure_ascii=False, indent=2)
        
        self.status['crawlers'][crawler_name]['runs'] += 1
        self.status['crawlers'][crawler_name]['last_run'] = record['timestamp']
        
        if success:
            self.status['crawlers'][crawler_name]['success'] += 1
        else:
            self.status['crawlers'][crawler_name]['failed'] += 1
    
    def run_bv_crawler(self, mid: str = '28346875', max_videos: int = 500) -> Dict:
        """
        执行BV号爬虫
        返回: {'success': bool, 'bvids': list, 'count': int, 'duration': float}
        """
        self.logger.info("="*60)
        self.logger.info("开始执行 BV号爬虫")
        self.logger.info("="*60)
        
        start_time = time.time()
        result = {'success': False, 'bvids': [], 'count': 0, 'duration': 0}
        
        try:
            from ytdlp_crawler import YtdlpBilibiliCrawler
            
            crawler = YtdlpBilibiliCrawler(cookie=self.cookie)
            videos = crawler.get_all_bvids(mid, max_videos)
            
            if videos:
                output_file = os.path.join(self.data_dir, 'all_bvids.json')
                crawler.save_bvids(videos, output_file)
                
                result['success'] = True
                result['bvids'] = [v['bvid'] for v in videos]
                result['count'] = len(videos)
                self.status['data_stats']['total_bvids'] = result['count']
                
                self.logger.info(f"[+] BV号爬虫完成，获取 {result['count']} 个视频")
            else:
                self.logger.warning("[!] BV号爬虫未获取到数据")
        
        except Exception as e:
            error_msg = f"BV号爬虫执行失败: {str(e)}"
            self.logger.error(f"[-] {error_msg}")
            self.logger.debug(traceback.format_exc())
            result['error'] = error_msg
        
        result['duration'] = time.time() - start_time
        self._record_execution('bv_crawler', result['success'], result['duration'], result['count'])
        
        return result
    
    def run_video_crawler(self, bvids: List[str] = None, max_videos: int = 10) -> Dict:
        """
        执行视频信息爬虫
        返回: {'success': bool, 'videos': list, 'count': int, 'duration': float}
        """
        self.logger.info("="*60)
        self.logger.info("开始执行 视频信息爬虫")
        self.logger.info("="*60)
        
        start_time = time.time()
        result = {'success': False, 'videos': [], 'count': 0, 'duration': 0}
        
        try:
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
                self.status['data_stats']['total_videos'] = result['count']
                
                self.logger.info(f"[+] 视频信息爬虫完成，获取 {result['count']} 个视频详情")
        
        except Exception as e:
            error_msg = f"视频信息爬虫执行失败: {str(e)}"
            self.logger.error(f"[-] {error_msg}")
            self.logger.debug(traceback.format_exc())
            result['error'] = error_msg
        
        result['duration'] = time.time() - start_time
        self._record_execution('video_crawler', result['success'], result['duration'], result['count'])
        
        return result
    
    def run_comment_crawler(self, bvids: List[str] = None, max_videos: int = 3) -> Dict:
        """
        执行评论区爬虫
        返回: {'success': bool, 'stories': list, 'count': int, 'duration': float}
        """
        self.logger.info("="*60)
        self.logger.info("开始执行 评论区爬虫")
        self.logger.info("="*60)
        
        start_time = time.time()
        result = {'success': False, 'stories': [], 'count': 0, 'duration': 0}
        
        try:
            sys.path.insert(0, self.scripts_dir)
            from crawler_v31 import BilibiliCommentCrawlerV31
            
            if not bvids:
                bvids_file = os.path.join(self.data_dir, 'all_bvids.json')
                if os.path.exists(bvids_file):
                    with open(bvids_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        bvids = data.get('bvid_list', [])[:max_videos]
            
            if not bvids:
                self.logger.warning("[!] 没有可用的BV号")
                return result
            
            crawler = BilibiliCommentCrawlerV31(cookie=self.cookie)
            
            all_results = []
            for i, bvid in enumerate(bvids[:max_videos], 1):
                self.logger.info(f"\n[{i}/{min(len(bvids), max_videos)}] 处理视频: {bvid}")
                
                try:
                    video_result = crawler.crawl_video_comments(bvid, max_pages=25)
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
                self.status['data_stats']['total_stories'] = total_stories
                
                self.logger.info(f"[+] 评论区爬虫完成，提取 {total_stories} 个故事")
        
        except Exception as e:
            error_msg = f"评论区爬虫执行失败: {str(e)}"
            self.logger.error(f"[-] {error_msg}")
            self.logger.debug(traceback.format_exc())
            result['error'] = error_msg
        
        result['duration'] = time.time() - start_time
        self._record_execution('comment_crawler', result['success'], result['duration'], result['count'])
        
        return result
    
    def run_full_pipeline(self, mid: str = '28346875', 
                          max_bvids: int = 500,
                          max_video_details: int = 10,
                          max_comment_videos: int = 3,
                          interval_between_crawlers: int = 5) -> Dict:
        """
        执行完整的爬虫流程
        
        Args:
            mid: UP主ID
            max_bvids: 最大BV号数量
            max_video_details: 最大视频详情数量
            max_comment_videos: 最大评论爬取视频数量
            interval_between_crawlers: 爬虫之间的间隔时间(秒)
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("怖客爬虫系统 - 开始执行完整流程")
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
            self.logger.info("\n[阶段 1/3] BV号爬虫")
            bv_result = self.run_bv_crawler(mid, max_bvids)
            pipeline_result['stages']['bv_crawler'] = bv_result
            
            if not bv_result['success']:
                pipeline_result['errors'].append("BV号爬虫失败")
                self.logger.warning("[!] BV号爬虫失败，使用已有数据...")
            
            time.sleep(interval_between_crawlers)
            
            # 阶段2: 视频信息爬虫
            self.logger.info("\n[阶段 2/3] 视频信息爬虫")
            video_result = self.run_video_crawler(
                bvids=bv_result.get('bvids', []),
                max_videos=max_video_details
            )
            pipeline_result['stages']['video_crawler'] = video_result
            
            if not video_result['success']:
                pipeline_result['errors'].append("视频信息爬虫失败")
            
            time.sleep(interval_between_crawlers)
            
            # 阶段3: 评论区爬虫
            self.logger.info("\n[阶段 3/3] 评论区爬虫")
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
            self.logger.debug(traceback.format_exc())
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
        
        self.logger.info(f"开始时间: {result['start_time']}")
        self.logger.info(f"结束时间: {result['end_time']}")
        self.logger.info(f"总耗时: {result['total_duration']:.2f} 秒")
        self.logger.info(f"状态: {'成功' if result['success'] else '失败'}")
        
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
        
        self.logger.info("\n数据统计:")
        self.logger.info(f"  BV号总数: {self.status['data_stats']['total_bvids']}")
        self.logger.info(f"  视频详情: {self.status['data_stats']['total_videos']}")
        self.logger.info(f"  故事数量: {self.status['data_stats']['total_stories']}")
        
        self.logger.info("\n累计执行统计:")
        self.logger.info(f"  总运行次数: {self.status['total_runs']}")
        self.logger.info(f"  成功次数: {self.status['successful_runs']}")
        self.logger.info(f"  失败次数: {self.status['failed_runs']}")
    
    def run_scheduled(self, interval_minutes: int = 60, 
                      max_iterations: int = None,
                      **pipeline_kwargs):
        """
        定时循环执行
        
        Args:
            interval_minutes: 执行间隔(分钟)
            max_iterations: 最大迭代次数(None表示无限)
            **pipeline_kwargs: 传递给run_full_pipeline的参数
        """
        self.logger.info("="*60)
        self.logger.info("怖客爬虫系统 - 定时执行模式")
        self.logger.info(f"执行间隔: {interval_minutes} 分钟")
        self.logger.info(f"最大迭代: {max_iterations or '无限'}")
        self.logger.info("="*60)
        
        iteration = 0
        
        while True:
            iteration += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"第 {iteration} 次执行")
            self.logger.info(f"{'='*60}")
            
            try:
                self.run_full_pipeline(**pipeline_kwargs)
            except Exception as e:
                self.logger.error(f"执行失败: {e}")
            
            if max_iterations and iteration >= max_iterations:
                self.logger.info(f"\n已达到最大迭代次数 {max_iterations}，停止执行")
                break
            
            self.logger.info(f"\n下次执行时间: {interval_minutes} 分钟后")
            self.logger.info(f"预计时间: {datetime.now().strftime('%H:%M:%S')} + {interval_minutes}分钟")
            
            time.sleep(interval_minutes * 60)


def main():
    """主函数"""
    print("="*60)
    print("怖客爬虫系统 - 主控程序")
    print("="*60)
    print("\n选择执行模式:")
    print("1. 执行一次完整流程")
    print("2. 定时循环执行")
    print("3. 仅执行BV号爬虫")
    print("4. 仅执行视频信息爬虫")
    print("5. 仅执行评论区爬虫")
    print("6. 查看执行状态")
    
    choice = input("\n请输入选项 (1-6): ").strip()
    
    orchestrator = CrawlerOrchestrator()
    
    if choice == '1':
        mid = input("输入UP主ID (默认: 28346875): ").strip() or '28346875'
        max_bvids = int(input("最大BV号数量 (默认: 500): ").strip() or '500')
        max_videos = int(input("最大视频详情数量 (默认: 10): ").strip() or '10')
        max_comments = int(input("最大评论爬取视频数 (默认: 3): ").strip() or '3')
        
        orchestrator.run_full_pipeline(
            mid=mid,
            max_bvids=max_bvids,
            max_video_details=max_videos,
            max_comment_videos=max_comments
        )
    
    elif choice == '2':
        interval = int(input("执行间隔(分钟) (默认: 60): ").strip() or '60')
        max_iter = input("最大迭代次数 (默认: 无限): ").strip()
        max_iter = int(max_iter) if max_iter else None
        
        orchestrator.run_scheduled(
            interval_minutes=interval,
            max_iterations=max_iter
        )
    
    elif choice == '3':
        orchestrator.run_bv_crawler()
    
    elif choice == '4':
        orchestrator.run_video_crawler()
    
    elif choice == '5':
        orchestrator.run_comment_crawler()
    
    elif choice == '6':
        print("\n执行状态:")
        print(json.dumps(orchestrator.status, ensure_ascii=False, indent=2))
    
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
