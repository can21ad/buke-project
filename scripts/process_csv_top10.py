#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV前10视频AI总结 - 用于网站全部视频区
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_video_summarizer_pro import VideoSummarizer, API_CONFIG

# 配置API
API_CONFIG['api_key'] = 'sk-mhrQtstUpfZqQHlsCgTTpz9mJilSJEoleUEm2WLhOGA8EmXz'
API_CONFIG['model'] = 'Kimi-K2.5'

# CSV前10个视频的BV号
CSV_TOP10_BVIDS = [
    'BV114411y7Se',   # 1
    'BV1194y1Z7No',   # 2
    'BV119feBnEF9',   # 3
    'BV11L25BaEqH',   # 4
    'BV11U4y1A7Bb',   # 5
    'BV11X4y1a7Sb',   # 6
    'BV11X4y1f7vt',   # 7
    'BV11t4y1977i',   # 8
    'BV12T4y1s7Vo',   # 9
    'BV12V411W7X7',   # 10
]

def process_csv_top10():
    """处理CSV前10个视频"""
    print("="*80)
    print("CSV前10视频AI总结 - 网站全部视频区")
    print("="*80)
    print(f"API: bobapi ({API_CONFIG['model']})")
    print(f"视频数: {len(CSV_TOP10_BVIDS)}")
    print()
    
    summarizer = VideoSummarizer()
    results = []
    
    for i, bvid in enumerate(CSV_TOP10_BVIDS, 1):
        print(f"\n{'#'*80}")
        print(f"# 处理 {i}/{len(CSV_TOP10_BVIDS)}")
        print(f"# BV号: {bvid}")
        print(f"{'#'*80}\n")
        
        result = summarizer.summarize_video(bvid, use_ai=True)
        
        if result:
            results.append({
                'rank': i,
                'bvid': result['bvid'],
                'title': result['title'],
                'owner': result['owner'],
                'duration': result['duration'],
                'view_count': result['view_count'],
                'summary': result['summary'],
                'generated_at': result['generated_at']
            })
            
            print(f"\n[OK] 视频: {result['title']}")
            print(f"[AI总结] {result['summary'][:100]}...")
        else:
            print(f"[FAIL] 处理失败: {bvid}")
        
        if i < len(CSV_TOP10_BVIDS):
            print(f"\n[WAIT] 等待3秒...")
            import time
            time.sleep(3)
    
    # 保存结果
    save_results(results)
    
    print(f"\n\n{'='*80}")
    print("处理完成")
    print(f"{'='*80}")
    print(f"成功: {len(results)}/{len(CSV_TOP10_BVIDS)}")
    
    return results

def save_results(results):
    """保存结果到JSON文件"""
    output = {
        'generated_at': __import__('datetime').datetime.now().isoformat(),
        'total': len(results),
        'summaries': results
    }
    
    # 保存到scripts目录
    output_path = os.path.join(
        os.path.dirname(__file__),
        'csv_top10_summaries.json'
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVE] 结果已保存: {output_path}")
    
    # 同时保存到web的data目录
    web_data_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'packages',
        'web',
        'public',
        'data',
        'csv_top10_summaries.json'
    )
    
    with open(web_data_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"[SAVE] 已同步到网站数据目录: {web_data_path}")

if __name__ == "__main__":
    process_csv_top10()