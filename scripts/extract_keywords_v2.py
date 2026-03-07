#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
继续为没有关键词的视频提取关键词
使用正确的评论API
"""

import requests
import time
import re
import json
import jieba
import jieba.analyse
from datetime import datetime
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

STOP_WORDS = set([
    "的", "了", "是", "我", "你", "他", "在", "和", "就", "都", "而", "及", "与", "着", 
    "这", "那", "一个", "啊", "哈", "哈哈", "哈哈哈", "视频", "UP主", "up", "怎么", "什么",
    "真的", "感觉", "觉得", "喜欢", "知道", "其实", "时候", "没有", "可以", "但是", "还是",
    "就是", "这个", "那个", "自己", "不过", "如果", "这么", "那么", "因为", "所以", "现在",
    "然后", "虽然", "最后", "这种", "那种", "有些", "大家", "一下", "有点", "而且", "出来",
    "进去", "起来", "一样", "一些", "已经", "不是", "为了", "或者", "还有", "那些", "这些",
    "什么", "怎么", "为何", "为什么", "特别", "非常", "比较", "应该", "可能", "一般", "一下",
    "一点", "两个", "三个", "四个", "五个", "六个", "七个", "八个", "九个", "十个", "几",
    "多少", "怎样", "如何", "哪里", "那里", "这里", "哪里", "哪儿", "谁", "哪个", "哪些",
    "能", "会", "要", "想", "去", "来", "说", "看", "听", "做", "让", "把", "被", "给",
    "从", "到", "向", "往", "对", "跟", "比", "按", "按着", "按照", "通过", "经过",
])

PERSONAL_WORDS = set([
    "大佬", "小伙伴", "阿澈", "投稿人", "哥们", "表哥", "表姐", "表弟", "表妹",
    "姐姐", "哥哥", "弟弟", "妹妹", "爸爸", "妈妈", "爷爷", "奶奶", "叔叔", "阿姨",
    "楼主", "博主", "主播", "up主", "作者", "粉丝", "观众", "用户", "网友",
    "稿主", "投稿", "投稿者", "朋友", "好友", "兄弟", "姐妹", "家人", "亲戚",
])


def get_video_info(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        if data['code'] == 0:
            return data['data']
    except Exception as e:
        print(f"获取视频信息异常: {e}")
    return None


def get_comments(aid, max_pages=5):
    comments_text = []
    
    for page in range(1, max_pages + 1):
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
                    content = reply['content']['message']
                    comments_text.append(content)
            else:
                print(f"  API错误: {data.get('message')}")
                break
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  抓取评论异常: {e}")
            break
            
    return comments_text


def clean_text(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
    return text


def extract_keywords(comments, top_k=5):
    if not comments:
        return []
    
    all_text = "。".join(comments)
    all_text = clean_text(all_text)
    
    if len(all_text) < 10:
        return []
    
    allowed_pos = ('n', 'nr', 'ns', 'nt', 'nz', 'vn')
    keywords = jieba.analyse.extract_tags(all_text, topK=top_k * 4, withWeight=True, allowPOS=allowed_pos)
    
    result = []
    for word, weight in keywords:
        if word not in STOP_WORDS and word not in PERSONAL_WORDS and len(word) > 1:
            result.append({
                'word': word,
                'weight': round(weight, 4)
            })
        if len(result) >= top_k:
            break
    
    return result


def main():
    db_path = '../packages/web/public/data/buke_all_episodes.json'
    
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data['videos']
    
    without_episode = [v for v in videos if not v.get('episode') or v['episode'] == 0]
    without_episode.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    
    need_process = [v for v in without_episode if not v.get('keywords') or len(v.get('keywords', [])) == 0]
    
    print(f"需要处理的视频数量: {len(need_process)}")
    print("=" * 50)
    
    success_count = 0
    fail_count = 0
    
    for i, video in enumerate(need_process):
        bvid = video['bvid']
        title = video['title'][:40]
        print(f"\n[{i+1}/{len(need_process)}] 处理: {title}...")
        print(f"  BV号: {bvid}")
        
        try:
            info = get_video_info(bvid)
            if not info:
                print(f"  获取视频信息失败")
                fail_count += 1
                time.sleep(2)
                continue
            
            aid = info['aid']
            reply_count = info['stat'].get('reply', 0)
            print(f"  评论数: {reply_count}")
            
            comments = get_comments(aid, max_pages=5)
            print(f"  获取到 {len(comments)} 条评论")
            
            keywords = extract_keywords(comments)
            video['keywords'] = keywords
            
            if keywords:
                kw_str = ", ".join([k['word'] for k in keywords])
                print(f"  关键词: {kw_str}")
                success_count += 1
            else:
                print(f"  关键词: 无")
                fail_count += 1
            
            time.sleep(2)
            
            if (i + 1) % 10 == 0:
                data['generated_at'] = datetime.now().isoformat()
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n  [已保存进度: {i+1}/{len(need_process)}]")
                print(f"  [休息20秒防止限流...]")
                time.sleep(20)
                
        except Exception as e:
            print(f"  处理失败: {e}")
            fail_count += 1
            time.sleep(5)
    
    data['generated_at'] = datetime.now().isoformat()
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print(f"数据库已更新: {db_path}")


if __name__ == '__main__':
    main()
