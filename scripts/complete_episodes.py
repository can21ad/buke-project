#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充缺失期数的视频信息
从B站获取151-169期的视频数据
"""

import yt_dlp
import json
import os
import re
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime


class EpisodeCompleter:
    """补充缺失期数的视频信息"""
    
    def __init__(self, mid: str = '28346875'):
        self.mid = mid
        self.space_url = f"https://space.bilibili.com/{mid}/upload/video"
        
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
            },
        }
    
    def get_all_videos_from_space(self, max_videos: int = 500) -> List[Dict]:
        """从UP主空间获取所有视频列表"""
        print(f"正在获取UP主 {self.mid} 的视频列表...")
        
        videos = []
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(self.space_url, download=False)
                
                if info and 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if i >= max_videos:
                            break
                        
                        if entry:
                            video_info = {
                                'bvid': entry.get('id', ''),
                                'title': entry.get('title', ''),
                                'url': entry.get('url', ''),
                                'duration': entry.get('duration', 0),
                                'view_count': entry.get('view_count', 0),
                                'upload_date': entry.get('upload_date', ''),
                            }
                            videos.append(video_info)
                            
                            if (i + 1) % 50 == 0:
                                print(f"已获取 {i + 1} 个视频...")
            
            print(f"共获取 {len(videos)} 个视频")
            
        except Exception as e:
            print(f"获取视频列表失败: {e}")
        
        return videos
    
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/',
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            
            if data['code'] == 0:
                info = data['data']
                return {
                    'bvid': bvid,
                    'title': info.get('title', ''),
                    'cover': info.get('pic', ''),
                    'play_count': info.get('stat', {}).get('view', 0),
                    'comment_count': info.get('stat', {}).get('danmaku', 0),
                    'duration': info.get('duration', 0),
                    'upload_date': datetime.fromtimestamp(info.get('pubdate', 0)).strftime('%Y-%m-%d'),
                    'desc': info.get('desc', ''),
                }
        except Exception as e:
            print(f"获取视频 {bvid} 详情失败: {e}")
        
        return {}
    
    def find_missing_episodes(self, videos: List[Dict], target_episodes: List[int]) -> Dict[int, List[Dict]]:
        """从视频列表中找出缺失期数的视频"""
        found = {}
        
        for video in videos:
            title = video.get('title', '')
            episode, part = self.extract_episode_info(title)
            
            if episode in target_episodes:
                if episode not in found:
                    found[episode] = []
                found[episode].append({
                    **video,
                    'episode': episode,
                    'part': part,
                })
        
        return found
    
    def run(self, target_episodes: List[int] = None):
        """运行补充任务"""
        if target_episodes is None:
            target_episodes = list(range(151, 170))
        
        print(f"目标期数: {target_episodes}")
        
        videos = self.get_all_videos_from_space(max_videos=500)
        
        found = self.find_missing_episodes(videos, target_episodes)
        
        print(f"\n找到的期数: {sorted(found.keys())}")
        
        missing = [ep for ep in target_episodes if ep not in found]
        if missing:
            print(f"仍未找到的期数: {missing}")
        
        result = []
        for episode in sorted(found.keys()):
            for video in found[episode]:
                print(f"\n获取第{episode}期{video['part']}详情: {video['bvid']}")
                details = self.get_video_details(video['bvid'])
                if details:
                    result.append({
                        'bvid': video['bvid'],
                        'video_url': f"https://www.bilibili.com/video/{video['bvid']}",
                        'cover_url': details.get('cover', ''),
                        'play_count': details.get('play_count', 0),
                        'comment_count': details.get('comment_count', 0),
                        'duration': details.get('duration', 0),
                        'title': details.get('title', ''),
                        'upload_date': details.get('upload_date', ''),
                        'episode': video['episode'],
                        'part': video['part'],
                    })
                    print(f"  标题: {details.get('title', '')[:50]}...")
                    print(f"  播放量: {details.get('play_count', 0)}")
                time.sleep(0.5)
        
        return result


def main():
    completer = EpisodeCompleter(mid='28346875')
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
