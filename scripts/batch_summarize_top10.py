#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOP10视频AI总结 - 批量处理
优先处理首页TOP10视频
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_video_summarizer_pro import VideoSummarizer, API_CONFIG
import json

# 配置API
API_CONFIG['api_key'] = 'sk-mhrQtstUpfZqQHlsCgTTpz9mJilSJEoleUEm2WLhOGA8EmXz'
API_CONFIG['model'] = 'Kimi-K2.5'

# TOP10视频的BV号（从top10_help_comments.json提取）
TOP10_BVIDS = [
    'BV1jG411c7Fj',   # Rank 1 - 道听途说87下
    'BV1D1qpB6ECc',   # Rank 2 - 道听途说165上
    'BV19SiFB1E1q',   # Rank 3 - 道听途说166下
    'BV1Gg6iB9EbS',   # Rank 4 - 道听途说特辑
    'BV1JK411e7Pm',   # Rank 5 - 道听途说84上
    'BV1yN4y1X7dR',   # Rank 6 - 道听途说159上
    'BV1ZV411L7rG',   # Rank 7 - 道听途说98上
    'BV1kG4y1j7fd',   # Rank 8 - 道听途说82上
    'BV1eP4y1Y7ds',   # Rank 9 - 道听途说86下
    'BV1rG411j7gV',   # Rank 10 - 道听途说88上
]

def batch_summarize_top10():
    """批量总结TOP10视频"""
    print("="*80)
    print("TOP10视频AI总结 - 批量处理")
    print("="*80)
    print(f"API: bobapi ({API_CONFIG['model']})")
    print(f"视频数: {len(TOP10_BVIDS)}")
    print()
    
    summarizer = VideoSummarizer()
    results = []
    
    for i, bvid in enumerate(TOP10_BVIDS, 1):
        print(f"\n{'#'*80}")
        print(f"# 处理 {i}/{len(TOP10_BVIDS)} - Rank {i}")
        print(f"# BV号: {bvid}")
        print(f"{'#'*80}\n")
        
        result = summarizer.summarize_video(bvid, use_ai=True)
        
        if result:
            results.append(result)
            
            # 打印结果
            print(f"\n[OK] 视频信息:")
            print(f"  标题: {result['title']}")
            print(f"  UP主: {result['owner']}")
            print(f"  播放量: {result['view_count']:,}")
            
            print(f"\n[AI故事总结]")
            print(result['summary'])
            
            # 保存到文件
            save_result(result, i)
        else:
            print(f"[FAIL] 处理失败: {bvid}")
        
        # 间隔避免请求过快
        if i < len(TOP10_BVIDS):
            print(f"\n[WAIT] 等待3秒...")
            import time
            time.sleep(3)
    
    # 生成完整报告
    generate_report(results)
    
    print(f"\n\n{'='*80}")
    print("批量处理完成")
    print(f"{'='*80}")
    print(f"成功: {len(results)}/{len(TOP10_BVIDS)}")
    print(f"报告文件: top10_ai_summaries_report.md")


def save_result(result: dict, rank: int):
    """保存单个结果"""
    output_dir = os.path.join(os.path.dirname(__file__), 'top10_summaries')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"rank{rank:02d}_{result['bvid']}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVE] 已保存: {filename}")


def generate_report(results: list):
    """生成完整报告"""
    report_path = os.path.join(
        os.path.dirname(__file__), 
        'top10_ai_summaries_report.md'
    )
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# TOP10视频AI故事总结报告\n\n")
        f.write(f"**生成时间**: {__import__('datetime').datetime.now().isoformat()}\n\n")
        f.write(f"**API**: bobapi ({API_CONFIG['model']})\n\n")
        f.write(f"**成功数**: {len(results)}/10\n\n")
        f.write("---\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"## Rank {i} - {result['bvid']}\n\n")
            f.write(f"**标题**: {result['title']}\n\n")
            f.write(f"**UP主**: {result['owner']}\n\n")
            f.write(f"**播放量**: {result['view_count']:,}\n\n")
            f.write(f"**时长**: {result['duration']}秒\n\n")
            f.write("**AI故事总结**:\n\n")
            f.write(f"{result['summary']}\n\n")
            f.write("---\n\n")
    
    print(f"\n[REPORT] 报告已生成: {report_path}")


if __name__ == "__main__":
    batch_summarize_top10()