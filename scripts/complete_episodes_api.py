#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充缺失期数的视频信息 - 使用B站API
从B站获取151-169期的视频数据
"""

import json
import os
import re
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime


class EpisodeCompleterAPI:
    """使用B站API补充缺失期数的视频信息"""
    
    def __init__(self, mid: str = '28346875'):
        self.mid = mid
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
        }
    
    def get_all_bvids(self, max_pages: int = 20) -> List[Dict]:
        """从UP主空间获取所有BV号"""
        print(f"正在获取UP主 {self.mid} 的视频列表...")
        
        all_videos = []
        page = 1
        ps = 50
        
        while page <= max_pages:
            url = f"https://api.bilibili.com/x/space/wbi/arc/search"
            params = {
                'mid': self.mid,
                'ps': ps,
                'pn': page,
                'order': 'pubdate',
                'platform': 'web',
                'web_location': '1550101',
                'order_avoided': 'true',
            }
            
            try:
                resp = requests.get(url, params=params, headers=self.headers, timeout=15)
                data = resp.json()
                
                if data['code'] != 0:
                    print(f"API错误: {data.get('message', 'unknown')}")
                    break
                
                vlist = data['data'].get('list', {}).get('vlist', [])
                if not vlist:
                    break
                
                for v in vlist:
                    all_videos.append({
                        'bvid': v.get('bvid', ''),
                        'title': v.get('title', ''),
                        'play_count': v.get('play', 0),
                        'duration': v.get('length', 0),
                        'upload_date': datetime.fromtimestamp(v.get('created', 0)).strftime('%Y-%m-%d'),
                    })
                
                print(f"第{page}页: 获取 {len(vlist)} 个视频，累计 {len(all_videos)} 个")
                
                if len(vlist) < ps:
                    break
                
                page += 1
                time.sleep(0.3)
                
            except Exception as e:
                print(f"获取第{page}页失败: {e}")
                break
        
        print(f"共获取 {len(all_videos)} 个视频")
        return all_videos
    
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
            resp = requests.get(url, headers=self.headers, timeout=10)
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
        
        videos = self.get_all_bvids(max_pages=30)
        
        found = self.find_missing_episodes(videos, target_episodes)
        
        print(f"\n找到的期数: {sorted(found.keys())}")
        
        missing = [ep for ep in target_episodes if ep not in found]
        if missing:
            print(f"仍未找到的期数: {missing}")
        
        covers_dir = '../packages/web/public/covers'
        os.makedirs(covers_dir, exist_ok=True)
        
        result = []
        for episode in sorted(found.keys()):
            for video in found[episode]:
                print(f"\n获取第{episode}期{video['part']}详情: {video['bvid']}")
                details = self.get_video_details(video['bvid'])
                if details:
                    cover_local = ''
                    if details.get('cover'):
                        cover_local = self.download_cover(details['cover'], video['bvid'], covers_dir)
                        if cover_local:
                            print(f"  封面已下载: {cover_local}")
                    
                    result.append({
                        'bvid': video['bvid'],
                        'video_url': f"https://www.bilibili.com/video/{video['bvid']}",
                        'cover_url': details.get('cover', ''),
                        'cover_local': cover_local,
                        'play_count': details.get('play_count', 0),
                        'comment_count': details.get('comment_count', 0),
                        'duration': details.get('duration', 0),
                        'duration_str': self.format_duration(details.get('duration', 0)),
                        'title': details.get('title', ''),
                        'upload_date': details.get('upload_date', ''),
                        'episode': video['episode'],
                        'part': video['part'],
                    })
                    print(f"  标题: {details.get('title', '')[:50]}...")
                    print(f"  播放量: {details.get('play_count', 0)}")
                time.sleep(0.3)
        
        return result
    
    def format_duration(self, seconds: int) -> str:
        """格式化时长"""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"


def main():
    completer = EpisodeCompleterAPI(mid='28346875')
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
