#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
继续为没有关键词的视频提取关键词
使用用户提供的Cookie认证
"""

import requests
import time
import re
import json
import jieba
import jieba.analyse
from datetime import datetime

COOKIE_STRING = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; __itrace_wid=f4622d5b-5e03-48ae-bc70-9524f49df407; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI5NjEwODMsImlhdCI6MTc3MjcwMTgyMywicGx0IjotMX0.VKjFOrbkVVIJv1clzx6_NSuzUKRf9xDFR-oS6KfLj7E; bili_ticket_expires=1772961023; SESSDATA=fe5df89b%2C1788276566%2Cc7940%2A32CjBO2upGc_KNO0p_ejpFjBrCmm_AvQ0jRmvBHkEIE9bQAWhSOXWYc9izhG2p_tmaxBQSVnltTTVNb2hfTUVtYjIxbFRkS0drQngxREJPcjZ0bk15WnZtall4a2ZWVTBlOG8tMTE4R2p5eHZ0VTVqWTBmV2lFaHNmcW9UdGV1a0ZmaWk2U2RQbTRRIIEC; bili_jct=fdd8571591004eff0bfd9c1c807eceb6; sid=79pa6pnf; bp_t_offset_16107971=1176340281939722240; b_lsid=10F54D397_19CBF0CD0DA; CURRENT_FNVAL=4048"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Cookie": COOKIE_STRING,
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

MIN_COMMENTS = 50


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


def get_comments(aid, min_count=MIN_COMMENTS):
    comments_text = []
    page = 1
    max_pages = 20
    
    while len(comments_text) < min_count and page <= max_pages:
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
                    cleaned = content.strip()
                    if len(cleaned) >= 5:
                        comments_text.append(cleaned)
            else:
                print(f"  API错误: code={data.get('code')}, msg={data.get('message')}")
                break
            
            page += 1
            time.sleep(0.8)
            
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
    if len(comments) < 20:
        return []
    
    all_text = "。".join(comments)
    all_text = clean_text(all_text)
    
    if len(all_text) < 50:
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
    
    need_process = [v for v in videos if not v.get('keywords') or len(v.get('keywords', [])) == 0]
    
    print(f"需要处理的视频数量: {len(need_process)}")
    print(f"每个视频最少获取 {MIN_COMMENTS} 条评论")
    print(f"使用Cookie认证")
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
            print(f"  视频评论总数: {reply_count}")
            
            if reply_count < 20:
                print(f"  评论数太少，跳过")
                fail_count += 1
                time.sleep(1)
                continue
            
            comments = get_comments(aid, min_count=MIN_COMMENTS)
            print(f"  有效评论数: {len(comments)}")
            
            if len(comments) < 20:
                print(f"  有效评论不足，跳过")
                fail_count += 1
                time.sleep(1)
                continue
            
            keywords = extract_keywords(comments)
            video['keywords'] = keywords
            
            if keywords:
                kw_str = ", ".join([k['word'] for k in keywords])
                print(f"  关键词: {kw_str}")
                success_count += 1
            else:
                print(f"  关键词提取失败")
                fail_count += 1
            
            time.sleep(1.5)
            
            if (i + 1) % 10 == 0:
                data['generated_at'] = datetime.now().isoformat()
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n  [进度: {i+1}/{len(need_process)}, 成功:{success_count}, 失败:{fail_count}]")
                print(f"  [休息15秒...]")
                time.sleep(15)
                
        except Exception as e:
            print(f"  处理失败: {e}")
            fail_count += 1
            time.sleep(3)
    
    data['generated_at'] = datetime.now().isoformat()
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print(f"数据库已更新: {db_path}")


if __name__ == '__main__':
    main()
