#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频总结测试脚本
测试前2个视频的AI总结功能
"""

import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_video_summarizer_pro import VideoSummarizer, VideoInfoExtractor, API_CONFIG

# 配置API密钥（使用bobapi）
API_CONFIG['api_key'] = 'sk-mhrQtstUpfZqQHlsCgTTpz9mJilSJEoleUEm2WLhOGA8EmXz'
API_CONFIG['model'] = 'Kimi-K2.5'

# 前2个BV号（从CSV数据库提取）
TEST_BVIDS = [
    'BV114411y7Se',  # 【都市传说】黑湖镇上的秘密第一集...
    'BV1194y1Z7No',  # 【道听途说70上】女同事出差后突发离奇行为...
]

def test_single_video(bvid):
    """测试单个视频总结"""
    print(f"\n{'='*60}")
    print(f"正在处理视频: {bvid}")
    print(f"{'='*60}\n")
    
    summarizer = VideoSummarizer()
    result = summarizer.summarize_video(bvid, use_ai=True)
    
    if result:
        print(f"\n[OK] 视频信息:")
        print(f"  标题: {result['title']}")
        print(f"  UP主: {result['owner']}")
        print(f"  播放量: {result['view_count']:,}")
        print(f"  时长: {result['duration']}秒")
        
        print(f"\n[AI总结]")
        print(f"  {result['summary']}")
        
        print(f"\n[元数据]")
        print(f"  内容来源: {result['content_source']}")
        print(f"  有字幕: {result['has_subtitle']}")
        print(f"  生成时间: {result['generated_at']}")
        
        return result
    else:
        print(f"[FAIL] 处理失败: {bvid}")
        return None

def main():
    """主函数"""
    print("AI视频总结工具 - 测试运行")
    print(f"API: bobapi ({API_CONFIG['model']})")
    print(f"测试视频数: {len(TEST_BVIDS)}")
    
    results = []
    
    for i, bvid in enumerate(TEST_BVIDS, 1):
        print(f"\n\n{'#'*60}")
        print(f"# 测试 {i}/{len(TEST_BVIDS)}")
        print(f"{'#'*60}")
        
        result = test_single_video(bvid)
        if result:
            results.append(result)
        
        # 间隔2秒避免请求过快
        if i < len(TEST_BVIDS):
            print(f"\n[WAIT] 等待2秒...")
            import time
            time.sleep(2)
    
    # 总结报告
    print(f"\n\n{'='*60}")
    print("测试完成报告")
    print(f"{'='*60}")
    print(f"成功: {len(results)}/{len(TEST_BVIDS)}")
    
    if results:
        print(f"\n所有AI总结预览:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   总结: {result['summary'][:100]}...")
            print()

if __name__ == "__main__":
    main()