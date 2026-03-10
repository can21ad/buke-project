#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI故事总结测试 - 改进版
测试新的提示词，专注提取具体故事
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_video_summarizer_pro import VideoSummarizer, API_CONFIG

# 配置API
API_CONFIG['api_key'] = 'sk-mhrQtstUpfZqQHlsCgTTpz9mJilSJEoleUEm2WLhOGA8EmXz'
API_CONFIG['model'] = 'Kimi-K2.5'

# 测试视频（道听途说70上 - 已知包含多个故事）
TEST_BVID = 'BV1194y1Z7No'

def test_story_summary():
    """测试故事总结"""
    print("="*60)
    print("AI故事总结测试 - 改进版")
    print("="*60)
    print(f"\n测试视频: {TEST_BVID}")
    print("预期: 包含多个故事，应该全部总结\n")
    
    summarizer = VideoSummarizer()
    result = summarizer.summarize_video(TEST_BVID, use_ai=True)
    
    if result:
        print("\n" + "="*60)
        print("视频信息:")
        print("="*60)
        print(f"标题: {result['title']}")
        print(f"UP主: {result['owner']}")
        print(f"播放量: {result['view_count']:,}")
        
        print("\n" + "="*60)
        print("AI故事总结:")
        print("="*60)
        print(result['summary'])
        
        print("\n" + "="*60)
        print("改进点检查:")
        print("="*60)
        summary = result['summary']
        
        # 检查是否包含模糊描述
        vague_words = ['氛围', '风格', '营造', '展现', '恐怖感', '悬疑感']
        found_vague = [w for w in vague_words if w in summary]
        if found_vague:
            print(f"[!] 仍包含模糊词汇: {', '.join(found_vague)}")
        else:
            print("[OK] 未检测到模糊描述词汇")
        
        # 检查是否包含多个故事标记
        story_markers = ['故事1', '故事2', '故事3', '第一个', '第二个', '第三个']
        found_markers = [m for m in story_markers if m in summary]
        if found_markers:
            print(f"[OK] 检测到故事分隔: {', '.join(found_markers)}")
        else:
            print("[!] 未检测到明确的故事分隔标记")
        
        # 检查字数
        print(f"[INFO] 总结字数: {len(summary)} 字")
        
    else:
        print("[FAIL] 处理失败")

if __name__ == "__main__":
    test_story_summary()