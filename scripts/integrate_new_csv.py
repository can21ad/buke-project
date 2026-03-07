#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合新CSV文件到数据库
处理 space (10).csv 并补充151-169期视频
"""

import csv
import json
import os
import re
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional


def parse_play_count(count_str: str) -> int:
    """解析播放量字符串"""
    count_str = count_str.strip()
    if not count_str:
        return 0
    
    if '万' in count_str:
        num = float(count_str.replace('万', ''))
        return int(num * 10000)
    elif '亿' in count_str:
        num = float(count_str.replace('亿', ''))
        return int(num * 100000000)
    else:
        try:
            return int(float(count_str))
        except:
            return 0


def parse_duration(duration_str: str) -> int:
    """解析时长字符串，返回秒数"""
    duration_str = duration_str.strip()
    if not duration_str:
        return 0
    
    parts = duration_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


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


def extract_bvid(url: str) -> str:
    """从URL中提取BV号"""
    match = re.search(r'BV[a-zA-Z0-9]{10}', url)
    return match.group(0) if match else ''


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


def parse_upload_date(date_str: str) -> str:
    """解析上传日期"""
    date_str = date_str.strip()
    if not date_str:
        return ''
    
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    if re.match(r'^\d{2}-\d{2}$', date_str):
        return f"2026-{date_str}"
    
    return date_str


def download_cover(cover_url: str, bvid: str, output_dir: str, headers: dict) -> str:
    """下载封面图片"""
    try:
        resp = requests.get(cover_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            ext = '.jpg'
            if '.png' in cover_url:
                ext = '.png'
            elif '.avif' in cover_url:
                ext = '.jpg'
            
            filename = f"{bvid}{ext}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            
            return f"covers/{filename}"
    except Exception as e:
        print(f"下载封面失败: {e}")
    
    return ''


def process_csv(csv_path: str, covers_dir: str) -> List[Dict]:
    """处理CSV文件"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/',
    }
    
    videos = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        
        for row in reader:
            if len(row) < 7:
                continue
            
            video_url = row[0].strip('"')
            cover_url = row[1].strip('"')
            play_count_str = row[2].strip('"')
            comment_count_str = row[3].strip('"')
            duration_str = row[4].strip('"')
            title = row[5].strip('"')
            upload_date_str = row[6].strip('"')
            
            bvid = extract_bvid(video_url)
            if not bvid:
                continue
            
            episode, part = extract_episode_info(title)
            
            play_count = parse_play_count(play_count_str)
            comment_count = parse_play_count(comment_count_str)
            duration = parse_duration(duration_str)
            upload_date = parse_upload_date(upload_date_str)
            
            cover_local = ''
            if cover_url:
                cover_local = download_cover(cover_url, bvid, covers_dir, headers)
                if cover_local:
                    print(f"下载封面: {bvid} - {title[:30]}...")
                time.sleep(0.2)
            
            videos.append({
                'bvid': bvid,
                'video_url': video_url,
                'cover_url': cover_url,
                'cover_local': cover_local,
                'play_count': play_count,
                'comment_count': comment_count,
                'duration': duration,
                'duration_str': format_duration(duration),
                'title': title,
                'upload_date': upload_date,
                'episode': episode,
                'part': part,
            })
    
    return videos


def merge_to_database(new_videos: List[Dict], db_path: str) -> Dict:
    """合并新视频到数据库"""
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    existing_bvids = {v['bvid'] for v in data['videos']}
    
    added = 0
    updated = 0
    
    for video in new_videos:
        if video['bvid'] in existing_bvids:
            for i, v in enumerate(data['videos']):
                if v['bvid'] == video['bvid']:
                    data['videos'][i] = video
                    updated += 1
                    break
        else:
            video['id'] = len(data['videos']) + 1
            data['videos'].append(video)
            existing_bvids.add(video['bvid'])
            added += 1
    
    data['total_videos'] = len(data['videos'])
    data['generated_at'] = datetime.now().isoformat()
    
    return data, added, updated


def main():
    csv_path = r'C:\Users\can\Downloads\space (10).csv'
    covers_dir = '../packages/web/public/covers'
    db_path = '../packages/web/public/data/buke_all_episodes.json'
    
    os.makedirs(covers_dir, exist_ok=True)
    
    print("处理CSV文件...")
    new_videos = process_csv(csv_path, covers_dir)
    print(f"共解析 {len(new_videos)} 个视频")
    
    print("\n合并到数据库...")
    data, added, updated = merge_to_database(new_videos, db_path)
    
    print(f"新增: {added} 个视频")
    print(f"更新: {updated} 个视频")
    print(f"总计: {data['total_videos']} 个视频")
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据库已保存: {db_path}")
    
    episodes = set()
    for v in data['videos']:
        if v.get('episode') and v['episode'] > 0:
            episodes.add(v['episode'])
    
    print(f"\n期数范围: {min(episodes)} - {max(episodes)}")
    print(f"总期数: {len(episodes)}")
    
    missing_151_169 = [i for i in range(151, 170) if i not in episodes]
    if missing_151_169:
        print(f"仍缺少的期数 (151-169): {missing_151_169}")
    else:
        print("151-169期已全部补齐！")


if __name__ == '__main__':
    main()
