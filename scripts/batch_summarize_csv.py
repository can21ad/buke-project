#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV视频批量AI总结
处理CSV数据库中的所有视频
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import csv
import json
import os
from datetime import datetime

# 导入AI总结工具
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_video_summarizer_pro import VideoSummarizer, API_CONFIG

# 配置API
API_CONFIG['api_key'] = 'sk-mhrQtstUpfZqQHlsCgTTpz9mJilSJEoleUEm2WLhOGA8EmXz'
API_CONFIG['model'] = 'Kimi-K2.5'

def read_csv_bvids(csv_path):
    """读取CSV文件获取所有BV号"""
    bvids = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'bvid' in row and row['bvid']:
                    bvids.append(row['bvid'])
        print(f"[OK] 成功读取CSV文件: {len(bvids)} 个视频")
        return bvids
    except Exception as e:
        print(f"[ERROR] 读取CSV失败: {e}")
        return []

def batch_summarize(bvids, batch_size=10):
    """批量处理视频总结"""
    summarizer = VideoSummarizer()
    results = []
    
    total = len(bvids)
    print(f"\n{'='*80}")
    print(f"开始批量处理: {total} 个视频")
    print(f"{'='*80}\n")
    
    for i, bvid in enumerate(bvids, 1):
        print(f"\n{'#'*80}")
        print(f"# 处理 {i}/{total} - {bvid}")
        print(f"{'#'*80}\n")
        
        try:
            result = summarizer.summarize_video(bvid, use_ai=True)
            
            if result:
                results.append({
                    'bvid': result['bvid'],
                    'title': result['title'],
                    'owner': result['owner'],
                    'duration': result['duration'],
                    'view_count': result['view_count'],
                    'summary': result['summary'],
                    'generated_at': result['generated_at']
                })
                print(f"\n[OK] 成功: {result['title']}")
            else:
                print(f"\n[FAIL] 失败: {bvid}")
                
        except Exception as e:
            print(f"\n[ERROR] 处理异常: {bvid} - {e}")
        
        # 每处理10个保存一次
        if i % batch_size == 0:
            save_progress(results, i)
            print(f"\n[SAVE] 已保存进度: {i}/{total}")
        
        # 避免API限流
        if i < total:
            print(f"\n[WAIT] 等待3秒...")
            import time
            time.sleep(3)
    
    return results

def save_progress(results, processed_count):
    """保存进度"""
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_processed': processed_count,
        'total_success': len(results),
        'summaries': results
    }
    
    # 保存到scripts目录
    output_path = os.path.join(
        os.path.dirname(__file__),
        'csv_all_summaries_progress.json'
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def save_final_results(results):
    """保存最终结果"""
    output = {
        'generated_at': datetime.now().isoformat(),
        'total': len(results),
        'summaries': results
    }
    
    # 保存到scripts目录
    output_path = os.path.join(
        os.path.dirname(__file__),
        'csv_all_summaries.json'
    )
    
    # 同时保存到web的data目录
    web_data_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'packages',
        'web',
        'public',
        'data',
        'csv_all_summaries.json'
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    with open(web_data_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[SAVE] 最终结果已保存:")
    print(f"  - {output_path}")
    print(f"  - {web_data_path}")

def main():
    """主函数"""
    csv_path = os.path.join(os.path.dirname(__file__), 'space_merged.csv')
    
    print("="*80)
    print("CSV视频批量AI总结工具")
    print("="*80)
    print(f"CSV文件: {csv_path}")
    print(f"API: bobapi ({API_CONFIG['model']})")
    print("="*80)
    
    # 读取CSV
    bvids = read_csv_bvids(csv_path)
    
    if not bvids:
        print("[ERROR] 没有读取到任何BV号，退出")
        return
    
    # 询问确认
    print(f"\n准备处理 {len(bvids)} 个视频")
    print("预计时间: {} 分钟".format(len(bvids) * 3 // 60))
    print("\n开始处理...\n")
    
    # 批量处理
    results = batch_summarize(bvids, batch_size=10)
    
    # 保存最终结果
    save_final_results(results)
    
    print(f"\n{'='*80}")
    print("处理完成!")
    print(f"{'='*80}")
    print(f"总计: {len(bvids)}")
    print(f"成功: {len(results)}")
    print(f"失败: {len(bvids) - len(results)}")
    print(f"成功率: {len(results)/len(bvids)*100:.1f}%")

if __name__ == "__main__":
    main()