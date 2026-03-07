#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充缺失期数的视频信息 - 使用已有BV号列表
从B站获取151-169期的视频数据
"""

import json
import os
import re
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime


class EpisodeCompleterFromBV:
    """使用已有BV号列表补充缺失期数的视频信息"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
        }
    
    def load_bvids(self, filepath: str = 'all_bvids.json') -> List[str]:
        """加载BV号列表"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [v['bvid'] for v in data.get('videos', [])]
    
    def extract_episode_info(self, title: str) -> tuple:
        """从标题中提取期数和上下集信息"""
        patterns = [
            r'【道听途说(\d+)(上|下)】',
            r'【道听途说(\d+)】',
            r'道听途说\s*(\d+)\s*(上|下)',
            r'道听途说\s*(\d+)',
            r'第(\d+)期',
            r'EP(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                episode = int(match.group(1))
                part = match.group(2) if len(match.groups()) > 1 and match.group(2) else ''
                return episode, part
        
        return 0, ''
    
    def get_video_details(self, bvid: str) -> Dict:
        """获取单个视频的详细信息"""
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        
        try:
            resp = self.session.get(url, headers=self.headers, timeout=10)
            data = resp.json()
            
            if data['code'] == 0:
                info = data['data']
                return {
                    'bvid': bvid,
                    'title': info.get('title', ''),
                    'cover': info.get('pic', ''),
                    'play_count': info.get('stat', {}).get('view', 0),
                    'comment_count': info.get('stat', {}).get('reply', 0),
                    'duration': info.get('duration', 0),
                    'upload_date': datetime.fromtimestamp(info.get('pubdate', 0)).strftime('%Y-%m-%d'),
                }
        except Exception as e:
            print(f"获取视频 {bvid} 详情失败: {e}")
        
        return {}
    
    def download_cover(self, cover_url: str, bvid: str, output_dir: str) -> str:
        """下载封面图片"""
        try:
            resp = requests.get(cover_url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                ext = '.jpg'
                if '.png' in cover_url:
                    ext = '.png'
                
                filename = f"{bvid}{ext}"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                
                return f"covers/{filename}"
        except Exception as e:
            print(f"下载封面失败: {e}")
        
        return ''
    
    def run(self, target_episodes: List[int] = None):
        """运行补充任务"""
        if target_episodes is None:
            target_episodes = list(range(151, 170))
        
        print(f"目标期数: {target_episodes}")
        
        bvids = self.load_bvids()
        print(f"加载了 {len(bvids)} 个BV号")
        
        covers_dir = '../packages/web/public/covers'
        os.makedirs(covers_dir, exist_ok=True)
        
        found = {}
        
        for i, bvid in enumerate(bvids):
            print(f"\r处理进度: {i+1}/{len(bvids)}", end='', flush=True)
            
            details = self.get_video_details(bvid)
            if details:
                title = details.get('title', '')
                episode, part = self.extract_episode_info(title)
                
                if episode in target_episodes:
                    if episode not in found:
                        found[episode] = []
                    
                    cover_local = ''
                    if details.get('cover'):
                        cover_local = self.download_cover(details['cover'], bvid, covers_dir)
                    
                    found[episode].append({
                        'bvid': bvid,
                        'video_url': f"https://www.bilibili.com/video/{bvid}",
                        'cover_url': details.get('cover', ''),
                        'cover_local': cover_local,
                        'play_count': details.get('play_count', 0),
                        'comment_count': details.get('comment_count', 0),
                        'duration': details.get('duration', 0),
                        'duration_str': self.format_duration(details.get('duration', 0)),
                        'title': details.get('title', ''),
                        'upload_date': details.get('upload_date', ''),
                        'episode': episode,
                        'part': part,
                    })
                    print(f"\n找到第{episode}期{part}: {title[:40]}...")
            
            time.sleep(0.2)
        
        print(f"\n\n找到的期数: {sorted(found.keys())}")
        
        missing = [ep for ep in target_episodes if ep not in found]
        if missing:
            print(f"仍未找到的期数: {missing}")
        
        result = []
        for episode in sorted(found.keys()):
            result.extend(found[episode])
        
        return result
    
    def format_duration(self, seconds: int) -> str:
        """格式化时长"""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"


def main():
    completer = EpisodeCompleterFromBV()
    new_videos = completer.run(target_episodes=list(range(151, 170)))
    
    if new_videos:
        output_file = 'missing_episodes_151_169.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_videos': len(new_videos),
                'videos': new_videos,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n保存到: {output_file}")
        print(f"共补充 {len(new_videos)} 个视频")
    else:
        print("\n未找到缺失期数的视频")


if __name__ == '__main__':
    main()
