#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找缺失的168期视频
"""

import json
import re
import time
import requests
from datetime import datetime


def extract_episode_info(title: str) -> tuple:
    """从标题中提取期数和上下集信息"""
    patterns = [
        (r'【道听途说(\d+)(上|下)】', True),
        (r'【道听途说(\d+)】', False),
        (r'道听途说\s*(\d+)\s*(上|下)', True),
        (r'道听途说\s*(\d+)', False),
    ]
    
    for pattern, has_part in patterns:
        match = re.search(pattern, title)
        if match:
            episode = int(match.group(1))
            part = match.group(2) if has_part and len(match.groups()) > 1 else ''
            return episode, part
    
    return 0, ''


def get_video_details(bvid: str) -> dict:
    """获取视频详情"""
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
                'comment_count': info.get('stat', {}).get('reply', 0),
                'duration': info.get('duration', 0),
                'upload_date': datetime.fromtimestamp(info.get('pubdate', 0)).strftime('%Y-%m-%d'),
            }
    except Exception as e:
        print(f"获取视频 {bvid} 详情失败: {e}")
    
    return {}


def main():
    with open('all_bvids.json', 'r', encoding='utf-8') as f:
        bvid_data = json.load(f)
    
    bvids = [v['bvid'] for v in bvid_data.get('videos', [])]
    print(f"共有 {len(bvids)} 个BV号")
    
    print("\n查找第168期...")
    found_168 = []
    
    for i, bvid in enumerate(bvids):
        print(f"\r进度: {i+1}/{len(bvids)}", end='', flush=True)
        
        details = get_video_details(bvid)
        if details:
            title = details.get('title', '')
            episode, part = extract_episode_info(title)
            
            if episode == 168:
                found_168.append({
                    'bvid': bvid,
                    'title': title,
                    'part': part,
                    **details
                })
                print(f"\n找到第168期{part}: {title[:50]}...")
        
        time.sleep(0.2)
    
    print(f"\n\n找到 {len(found_168)} 个第168期视频")
    
    if found_168:
        with open('episode_168.json', 'w', encoding='utf-8') as f:
            json.dump(found_168, f, ensure_ascii=False, indent=2)
        print("已保存到 episode_168.json")


if __name__ == '__main__':
    main()
