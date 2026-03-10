#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成AI总结数据
为TOP10视频生成AI总结
"""

import json
import os
from datetime import datetime
from pathlib import Path

def generate_ai_summaries():
    """生成AI总结数据"""
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    web_public_dir = project_root / "packages" / "web" / "public" / "data"
    
    # 读取TOP10数据
    top10_path = web_public_dir / "top10_help_comments.json"
    with open(top10_path, 'r', encoding='utf-8') as f:
        top10_data = json.load(f)
    
    # 读取现有的AI总结数据（如果有）
    ai_summaries_path = project_root / "ai_summaries.json"
    existing_summaries = {}
    if ai_summaries_path.exists():
        with open(ai_summaries_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            for summary in existing_data.get('summaries', []):
                existing_summaries[summary['bvid']] = summary
    
    # 生成新的总结
    summaries = []
    for video in top10_data['videos']:
        bvid = video['bvid']
        
        # 如果已有总结，使用现有的
        if bvid in existing_summaries:
            summaries.append(existing_summaries[bvid])
            continue
        
        # 生成新的AI总结
        title = video['title']
        episode = video.get('episode', 0)
        comment_count = video.get('comment_count', 0)
        comments = video.get('comments', [])
        
        # 从标题提取信息
        episode_info = f"第{episode}期" if episode > 0 else "特别期"
        
        # 从评论中提取关键词
        keywords = extract_keywords_from_comments(comments)
        
        # 生成总结文本（50字以内）
        summary_text = generate_summary_text(title, episode_info, comment_count, keywords)
        
        # 创建总结对象
        summary = {
            "bvid": bvid,
            "title": title,
            "summary": summary_text,
            "generated_at": datetime.now().isoformat(),
            "keywords": keywords[:5]  # 只保留前5个关键词
        }
        
        summaries.append(summary)
    
    # 创建输出数据
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_videos": len(summaries),
        "success_count": len(summaries),
        "summaries": summaries
    }
    
    # 保存到文件
    with open(ai_summaries_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # 同时保存到web public目录
    web_ai_path = web_public_dir / "ai_summaries.json"
    with open(web_ai_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] 已生成 {len(summaries)} 个AI总结")
    print(f"[FILE] 保存到: {ai_summaries_path}")
    print(f"[WEB] 同时保存到: {web_ai_path}")

def extract_keywords_from_comments(comments):
    """从评论中提取关键词"""
    if not comments:
        return ["恐怖", "灵异", "故事"]
    
    keyword_count = {}
    
    for comment in comments:
        # 使用评论中的keyword字段
        if 'keyword' in comment and comment['keyword']:
            keyword = comment['keyword']
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # 从评论内容中提取关键词
        if 'content' in comment:
            content = comment['content']
            # 简单的中文分词（按标点分割）
            words = [word for word in content.split() if 2 <= len(word) <= 4]
            for word in words:
                keyword_count[word] = keyword_count.get(word, 0) + 1
    
    # 按频率排序
    sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
    
    # 提取前10个关键词
    keywords = [kw for kw, count in sorted_keywords[:10]]
    
    # 如果没有提取到关键词，使用默认关键词
    if not keywords:
        keywords = ["恐怖", "灵异", "诡异", "超自然", "故事"]
    
    return keywords

def generate_summary_text(title, episode_info, comment_count, keywords):
    """生成总结文本"""
    
    # 从标题中提取主要内容
    title_clean = title.replace('【', '').replace('】', '').replace('（', '').replace('）', '')
    
    # 使用不同的总结模板
    templates = [
        f"{episode_info}精选内容，聚焦{keywords[0] if keywords else '恐怖'}主题，收到{comment_count}条观众互动。",
        f"本期探讨{keywords[0] if len(keywords) > 0 else '灵异'}现象，涉及{keywords[1] if len(keywords) > 1 else '超自然'}元素，社区讨论热烈。",
        f"{episode_info}恐怖故事合集，涵盖{', '.join(keywords[:3]) if keywords else '多种灵异'}话题，引发观众深度讨论。",
        f"以{keywords[0] if keywords else '诡异'}事件为核心，{episode_info}呈现{comment_count}条求助评论，展现社区活跃度。",
        f"灵异内容聚合，包含{len(keywords)}个热门关键词，{episode_info}获得高度关注。"
    ]
    
    # 选择模板（基于标题长度和关键词数量）
    template_index = (len(title) + len(keywords)) % len(templates)
    summary = templates[template_index]
    
    # 确保总结在50字以内
    if len(summary) > 50:
        summary = summary[:47] + "..."
    
    return summary

if __name__ == "__main__":
    print("开始生成AI总结数据...")
    generate_ai_summaries()
    print("AI总结数据生成完成！")