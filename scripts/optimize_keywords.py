#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词审核与优化脚本
1. 筛选重复与低价值词汇
2. 提炼核心关键词
3. 从已有评论数据重新提取
4. 质量控制与验证
"""

import json
import re
import jieba
import jieba.analyse
from collections import Counter, defaultdict
from datetime import datetime

# 低价值通用词汇（需要移除）
LOW_VALUE_WORDS = set([
    "故事", "东西", "男生", "女生", "小说", "男人", "女人", "小孩", "孩子",
    "啊啊啊", "弹幕", "封面", "高能", "小时候", "啊啊", "哈哈哈",
    "评论", "视频", "内容", "部分", "地方", "事情", "情况", "问题",
    "时候", "样子", "方面", "时间", "经历", "事件", "现象", "结果",
    "过程", "状态", "感觉", "印象", "记忆", "想法", "观点", "看法",
])

# 人称代词（需要移除）
PERSONAL_WORDS = set([
    "大佬", "小伙伴", "阿澈", "投稿人", "哥们", "表哥", "表姐", "表弟", "表妹",
    "姐姐", "哥哥", "弟弟", "妹妹", "爸爸", "妈妈", "爷爷", "奶奶", "叔叔", "阿姨",
    "楼主", "博主", "主播", "up主", "作者", "粉丝", "观众", "用户", "网友",
    "稿主", "投稿", "投稿者", "朋友", "好友", "兄弟", "姐妹", "家人", "亲戚",
    "男主", "女主", "主角", "主人公",
])

# 停用词
STOP_WORDS = set([
    "的", "了", "是", "我", "你", "他", "在", "和", "就", "都", "而", "及", "与", "着", 
    "这", "那", "一个", "啊", "哈", "哈哈", "哈哈哈", "怎么", "什么",
    "真的", "感觉", "觉得", "喜欢", "知道", "其实", "没有", "可以", "但是", "还是",
    "就是", "这个", "那个", "自己", "不过", "如果", "这么", "那么", "因为", "所以", "现在",
    "然后", "虽然", "最后", "这种", "那种", "有些", "大家", "一下", "有点", "而且", "出来",
    "进去", "起来", "一样", "一些", "已经", "不是", "为了", "或者", "还有", "那些", "这些",
    "特别", "非常", "比较", "应该", "可能", "一般", "一点", "几", "多少", "怎样", "如何",
    "哪里", "那里", "这里", "哪儿", "谁", "哪个", "哪些", "能", "会", "要", "想", "去", "来",
    "说", "看", "听", "做", "让", "把", "被", "给", "从", "到", "向", "往", "对", "跟", "比",
])

# 合并所有需要过滤的词
ALL_FILTER_WORDS = LOW_VALUE_WORDS | PERSONAL_WORDS | STOP_WORDS


def load_database():
    """加载数据库"""
    db_path = '../packages/web/public/data/buke_all_episodes.json'
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_database(data):
    """保存数据库"""
    db_path = '../packages/web/public/data/buke_all_episodes.json'
    data['generated_at'] = datetime.now().isoformat()
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def analyze_keyword_frequency(videos):
    """分析关键词频率"""
    keyword_counter = Counter()
    keyword_video_count = defaultdict(int)
    
    for video in videos:
        keywords = video.get('keywords', [])
        for kw in keywords:
            word = kw['word']
            keyword_counter[word] += 1
            keyword_video_count[word] += 1
    
    return keyword_counter, keyword_video_count


def identify_high_frequency_words(keyword_counter, total_videos, threshold=0.1):
    """识别高频低价值词汇"""
    high_freq_words = set()
    threshold_count = int(total_videos * threshold)
    
    for word, count in keyword_counter.items():
        if count >= threshold_count:
            high_freq_words.add(word)
    
    return high_freq_words


def clean_text(text):
    """清洗文本"""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
    return text


def extract_quality_keywords(text, top_k=5):
    """提取高质量关键词"""
    if len(text) < 50:
        return []
    
    allowed_pos = ('n', 'nr', 'ns', 'nt', 'nz', 'vn')
    keywords = jieba.analyse.extract_tags(text, topK=top_k * 6, withWeight=True, allowPOS=allowed_pos)
    
    result = []
    for word, weight in keywords:
        if (word not in ALL_FILTER_WORDS and 
            len(word) > 1 and 
            not word.isdigit()):
            result.append({
                'word': word,
                'weight': round(weight, 4)
            })
        if len(result) >= top_k:
            break
    
    return result


def optimize_video_keywords(video, high_freq_words):
    """优化单个视频的关键词"""
    original_keywords = video.get('keywords', [])
    
    filtered_keywords = [
        kw for kw in original_keywords 
        if kw['word'] not in ALL_FILTER_WORDS 
        and kw['word'] not in high_freq_words
    ]
    
    if len(filtered_keywords) >= 3:
        return filtered_keywords[:5], 'filtered'
    
    comments = video.get('_comments', [])
    if comments:
        all_text = "。".join(comments)
        all_text = clean_text(all_text)
        new_keywords = extract_quality_keywords(all_text, top_k=5)
        if new_keywords:
            return new_keywords, 're_extracted'
    
    return filtered_keywords if filtered_keywords else original_keywords[:3], 'kept_original'


def generate_report(videos, stats):
    """生成优化报告"""
    report = []
    report.append("=" * 60)
    report.append("关键词优化报告")
    report.append("=" * 60)
    report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"总视频数: {len(videos)}")
    report.append(f"\n--- 优化统计 ---")
    report.append(f"过滤处理: {stats['filtered']} 个视频")
    report.append(f"重新提取: {stats['re_extracted']} 个视频")
    report.append(f"保持原样: {stats['kept_original']} 个视频")
    report.append(f"\n--- 高频词识别 ---")
    for word, count in stats['high_freq_words'][:20]:
        report.append(f"  {word}: 出现在 {count} 个视频中")
    report.append(f"\n--- 低价值词汇列表 ---")
    report.append(f"共 {len(LOW_VALUE_WORDS)} 个低价值词汇")
    report.append(f"共 {len(PERSONAL_WORDS)} 个人称代词")
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


def main():
    print("加载数据库...")
    data = load_database()
    videos = data['videos']
    
    print(f"总视频数: {len(videos)}")
    
    print("\n1. 分析关键词频率...")
    keyword_counter, keyword_video_count = analyze_keyword_frequency(videos)
    
    print(f"   发现 {len(keyword_counter)} 个不同关键词")
    
    print("\n2. 识别高频低价值词汇...")
    high_freq_words = identify_high_frequency_words(keyword_counter, len(videos), threshold=0.15)
    high_freq_list = [(w, keyword_video_count[w]) for w in high_freq_words]
    high_freq_list.sort(key=lambda x: x[1], reverse=True)
    
    print(f"   发现 {len(high_freq_words)} 个高频词（出现在超过15%的视频中）")
    for word, count in high_freq_list[:10]:
        print(f"   - {word}: {count} 次")
    
    print("\n3. 优化关键词...")
    stats = {
        'filtered': 0,
        're_extracted': 0,
        'kept_original': 0,
        'high_freq_words': high_freq_list,
    }
    
    for i, video in enumerate(videos):
        if (i + 1) % 100 == 0:
            print(f"   处理进度: {i+1}/{len(videos)}")
        
        new_keywords, action = optimize_video_keywords(video, high_freq_words)
        video['keywords'] = new_keywords
        stats[action] += 1
    
    print(f"\n   过滤处理: {stats['filtered']} 个")
    print(f"   重新提取: {stats['re_extracted']} 个")
    print(f"   保持原样: {stats['kept_original']} 个")
    
    print("\n4. 验证优化结果...")
    new_counter, _ = analyze_keyword_frequency(videos)
    
    removed_count = 0
    for word in ALL_FILTER_WORDS:
        if word in keyword_counter:
            old_count = keyword_counter[word]
            new_count = new_counter.get(word, 0)
            if old_count != new_count:
                removed_count += old_count - new_count
    
    print(f"   移除低价值词汇出现次数: {removed_count}")
    
    print("\n5. 保存数据库...")
    save_database(data)
    print("   数据库已更新")
    
    print("\n6. 生成报告...")
    report = generate_report(videos, stats)
    print(report)
    
    with open('keyword_optimization_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("\n报告已保存到: keyword_optimization_report.txt")


if __name__ == '__main__':
    main()
