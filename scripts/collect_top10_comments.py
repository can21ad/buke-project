#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大家都在看TOP10 - 评论采集脚本
采集播放量TOP10的道听途说视频中包含特定关键词的评论
"""

import requests
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict

COOKIE_STRING = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; __itrace_wid=f4622d5b-5e03-48ae-bc70-9524f49df407; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI5NjEwODMsImlhdCI6MTc3MjcwMTgyMywicGx0IjotMX0.VKjFOrbkVVIJv1clzx6_NSuzUKRf9xDFR-oS6KfLj7E; bili_ticket_expires=1772961023; SESSDATA=fe5df89b%2C1788276566%2Cc7940%2A32CjBO2upGc_KNO0p_ejpFjBrCmm_AvQ0jRmvBHkEIE9bQAWhSOXWYc9izhG2p_tmaxBQSVnltTTVNb2hfTUVtYjIxbFRkS0drQngxREJPcjZ0bk15WnZtall4a2ZWVTBlOG8tMTE4R2p5eHZ0VTVqWTBmV2lFaHNmcW9UdGV1a0ZmaWk2U2RQbTRRIIEC; bili_jct=fdd8571591004eff0bfd9c1c807eceb6; sid=79pa6pnf; bp_t_offset_16107971=1176340281939722240; b_lsid=10F54D397_19CBF0CD0DA; CURRENT_FNVAL=4048"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Cookie": COOKIE_STRING,
}

SEARCH_KEYWORDS = [
    "求助", "找出处", "有谁还记得", "找不到", "求出处",
    "谁知道", "求告知", "有没有人知道", "帮忙找", "想找",
    "忘记叫什么", "不记得", "以前看过", "很久以前", "小时候看过",
    "名字叫什么", "是什么故事", "哪个故事", "哪一期",
]


def load_database():
    """加载数据库"""
    db_path = '../packages/web/public/data/buke_all_episodes.json'
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_top10_videos(data):
    """获取播放量TOP10的道听途说视频"""
    videos = data['videos']
    
    daoting_videos = [v for v in videos if '道听途说' in v.get('title', '')]
    
    daoting_videos.sort(key=lambda x: x.get('play_count', 0), reverse=True)
    
    top10 = daoting_videos[:10]
    
    return top10


def get_video_info(bvid):
    """获取视频详细信息"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        if data['code'] == 0:
            return data['data']
    except Exception as e:
        print(f"获取视频信息异常: {e}")
    return None


def contains_keyword(text):
    """检查文本是否包含关键词"""
    text_lower = text.lower()
    for kw in SEARCH_KEYWORDS:
        if kw in text_lower:
            return True, kw
    return False, None


def get_replies(aid, root_id):
    """获取评论的回复"""
    url = "https://api.bilibili.com/x/v2/reply/reply"
    params = {
        "type": 1,
        "oid": aid,
        "root": root_id,
        "pn": 1,
        "ps": 20,
    }
    
    replies = []
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        data = resp.json()
        
        if data.get('code') == 0:
            replies_data = data['data'].get('replies', [])
            for r in replies_data:
                replies.append({
                    'id': r.get('rpid', 0),
                    'content': r.get('content', {}).get('message', ''),
                    'author': r.get('member', {}).get('uname', ''),
                    'like': r.get('like', 0),
                    'time': r.get('ctime', 0),
                })
    except Exception as e:
        print(f"    获取回复异常: {e}")
    
    return replies


def get_comments(aid, bvid, episode, min_count=200):
    """获取包含关键词的评论"""
    comments = []
    page = 1
    max_pages = 50
    
    while len(comments) < min_count and page <= max_pages:
        url = "https://api.bilibili.com/x/v2/reply"
        params = {
            "type": 1,
            "oid": aid,
            "pn": page,
            "ps": 20,
            "sort": 2,
        }
        
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            data = resp.json()
            
            if data.get('code') == 0:
                replies = data['data'].get('replies', [])
                if not replies:
                    break
                
                for reply in replies:
                    content = reply.get('content', {}).get('message', '')
                    has_keyword, keyword = contains_keyword(content)
                    
                    if has_keyword:
                        reply_count = reply.get('rcount', 0)
                        
                        comment_data = {
                            'id': reply.get('rpid', 0),
                            'content': content,
                            'author': reply.get('member', {}).get('uname', ''),
                            'like': reply.get('like', 0),
                            'time': reply.get('ctime', 0),
                            'keyword': keyword,
                            'reply_count': reply_count,
                            'has_replies': reply_count > 0,
                            'replies': [],
                            'weight': 1 + (reply_count * 0.5),
                        }
                        
                        if reply_count > 0:
                            sub_replies = get_replies(aid, reply.get('rpid', 0))
                            comment_data['replies'] = sub_replies
                            comment_data['weight'] += len(sub_replies) * 0.3
                        
                        comments.append(comment_data)
            else:
                print(f"    API错误: {data.get('message')}")
                break
            
            page += 1
            time.sleep(0.8)
            
        except Exception as e:
            print(f"    抓取评论异常: {e}")
            break
    
    comments.sort(key=lambda x: x['weight'], reverse=True)
    
    return comments[:min_count]


def main():
    print("=" * 60)
    print("大家都在看TOP10 - 评论采集")
    print("=" * 60)
    
    print("\n1. 加载数据库...")
    data = load_database()
    
    print("\n2. 获取播放量TOP10的道听途说视频...")
    top10 = get_top10_videos(data)
    
    print(f"   找到 {len(top10)} 个视频:")
    for i, v in enumerate(top10):
        print(f"   {i+1}. 第{v.get('episode', 0)}期 - {v['title'][:30]}... (播放: {v.get('play_count', 0)})")
    
    print("\n3. 采集评论数据...")
    results = []
    
    for i, video in enumerate(top10):
        bvid = video['bvid']
        episode = video.get('episode', 0)
        title = video['title']
        
        print(f"\n   [{i+1}/10] 处理第{episode}期: {title[:30]}...")
        
        info = get_video_info(bvid)
        if not info:
            print(f"    获取视频信息失败，跳过")
            continue
        
        aid = info['aid']
        reply_count = info['stat'].get('reply', 0)
        print(f"    评论总数: {reply_count}")
        
        comments = get_comments(aid, bvid, episode, min_count=200)
        print(f"    符合条件的评论: {len(comments)} 条")
        
        if comments:
            results.append({
                'rank': i + 1,
                'bvid': bvid,
                'aid': aid,
                'episode': episode,
                'title': title,
                'play_count': video.get('play_count', 0),
                'cover_url': video.get('cover_url', ''),
                'cover_local': video.get('cover_local', ''),
                'comment_count': len(comments),
                'comments': comments,
            })
        
        time.sleep(2)
    
    print("\n4. 保存数据...")
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_videos': len(results),
        'total_comments': sum(v['comment_count'] for v in results),
        'keywords': SEARCH_KEYWORDS,
        'videos': results,
    }
    
    output_path = '../packages/web/public/data/top10_help_comments.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"   数据已保存: {output_path}")
    
    print("\n" + "=" * 60)
    print("采集完成!")
    print(f"视频数: {len(results)}")
    print(f"评论数: {sum(v['comment_count'] for v in results)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
