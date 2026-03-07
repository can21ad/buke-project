#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速查找第168期视频
"""

import json
import re
import time
import requests
from datetime import datetime


def download_cover(cover_url: str, bvid: str, output_dir: str, headers: dict) -> str:
    """下载封面图片"""
    try:
        resp = requests.get(cover_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            filename = f"{bvid}.jpg"
            filepath = f"{output_dir}/{filename}"
            
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            
            return f"covers/{filename}"
    except Exception as e:
        print(f"下载封面失败: {e}")
    
    return ''


def format_duration(seconds: int) -> str:
    """格式化时长"""
    if seconds >= 3600:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{mins:02d}:{secs:02d}"
    else:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"


def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/',
    }
    
    covers_dir = '../packages/web/public/covers'
    
    keywords = [
        '道听途说168',
        '道听途说 168',
        '道听途说第168期',
    ]
    
    found_videos = []
    
    for keyword in keywords:
        print(f"搜索: {keyword}")
        url = f"https://api.bilibili.com/x/web-interface/search/type"
        params = {
            'keyword': keyword,
            'search_type': 'video',
            'page': 1,
            'page_size': 20,
        }
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()
            
            if data['code'] == 0:
                results = data['data'].get('result', [])
                for r in results:
                    title = r.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
                    bvid = r.get('bvid', '')
                    
                    if '168' in title and '道听途说' in title:
                        print(f"  找到: {title[:50]}... ({bvid})")
                        
                        match_upper = re.search(r'【道听途说168(上|下)】', title)
                        match_single = re.search(r'【道听途说168】', title)
                        
                        if match_upper:
                            part = match_upper.group(1)
                        elif match_single:
                            part = ''
                        else:
                            part = ''
                        
                        video_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
                        vresp = requests.get(video_url, headers=headers, timeout=10)
                        vdata = vresp.json()
                        
                        if vdata['code'] == 0:
                            info = vdata['data']
                            cover_url = info.get('pic', '')
                            cover_local = download_cover(cover_url, bvid, covers_dir, headers) if cover_url else ''
                            
                            found_videos.append({
                                'bvid': bvid,
                                'video_url': f"https://www.bilibili.com/video/{bvid}",
                                'cover_url': cover_url,
                                'cover_local': cover_local,
                                'play_count': info.get('stat', {}).get('view', 0),
                                'comment_count': info.get('stat', {}).get('reply', 0),
                                'duration': info.get('duration', 0),
                                'duration_str': format_duration(info.get('duration', 0)),
                                'title': info.get('title', ''),
                                'upload_date': datetime.fromtimestamp(info.get('pubdate', 0)).strftime('%Y-%m-%d'),
                                'episode': 168,
                                'part': part,
                            })
                        
                        time.sleep(0.3)
        
        except Exception as e:
            print(f"搜索失败: {e}")
        
        time.sleep(0.5)
    
    print(f"\n找到 {len(found_videos)} 个第168期视频")
    
    if found_videos:
        with open('episode_168.json', 'w', encoding='utf-8') as f:
            json.dump(found_videos, f, ensure_ascii=False, indent=2)
        print("已保存到 episode_168.json")
        
        db_path = '../packages/web/public/data/buke_all_episodes.json'
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        existing_bvids = {v['bvid'] for v in db_data['videos']}
        
        for video in found_videos:
            if video['bvid'] not in existing_bvids:
                video['id'] = len(db_data['videos']) + 1
                db_data['videos'].append(video)
                print(f"添加: {video['title'][:40]}...")
        
        db_data['total_videos'] = len(db_data['videos'])
        db_data['generated_at'] = datetime.now().isoformat()
        
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据库已更新，总计 {db_data['total_videos']} 个视频")


if __name__ == '__main__':
    main()
