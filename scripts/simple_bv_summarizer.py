#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版BV号故事提取器
功能：输入BV号 -> 获取视频信息 -> 调用AI总结 -> 输出故事内容
"""

import requests
import json
import re
import sys

# API配置
API_CONFIG = {
    "base_url": "https://openrouter.fans/v1",
    "api_key": "sk-S6Q7NxPxQUNY7gWP1RRC3cTeRuJ2mjPY42CRS3WShl5KrSE3",
    "model": "deepseek/deepseek-chat"
}

def get_video_info(bvid):
    """获取B站视频信息"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        if data['code'] == 0:
            video_data = data['data']
            return {
                'bvid': bvid,
                'title': video_data['title'],
                'description': video_data.get('desc', ''),
                'duration': video_data.get('duration', 0),
                'owner': video_data['owner']['name']
            }
    except Exception as e:
        print(f"[-] 获取视频信息失败: {e}", file=sys.stderr)
    return None

def generate_summary(content, title):
    """使用AI生成详细故事总结"""
    prompt = f"""请分析以下视频内容，提取并总结其中的所有故事，要求尽可能详细地描述故事情节，不遗漏任何重要细节。

视频标题：{title}

视频内容：
{content[:8000]}

要求：
1. **详细总结具体故事内容**，不要描述风格、氛围、制作等总体评价
2. **识别所有故事**：如果视频包含2-3个故事，必须全部列出，不能只挑一个
3. **每个故事总结格式**：
   - 故事X：[详细的故事情节描述，包含关键细节和发展过程]
   - 关键元素：人物、地点、事件、时间顺序
4. **去除模糊描述**：不要"营造出恐怖氛围"、"展现了...风格"等空洞描述
5. **专注事实**：只描述发生了什么，不要评价或感受
6. **尽可能详细**：包含故事的开始、发展、高潮和结局，不遗漏任何重要细节

示例格式：
故事1：主角在一个雨夜回家，发现家附近有一个穿着黑色大衣的女子在监视自己。主角感到不安，加快脚步回家。第二天，主角再次看到该女子，发现她没有眼睛，眼眶空洞。主角报警，但警方赶到时女子已消失。晚上，主角听到敲门声，开门后发现女子站在门口，伸出手向主角靠近...
故事2：...

请生成详细的故事总结："""

    try:
        base_url = API_CONFIG['base_url'].rstrip('/')
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_CONFIG['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://buke.app",
            "X-Title": "Buke AI Summarizer"
        }
        data = {
            "model": API_CONFIG['model'],
            "messages": [
                {"role": "system", "content": "你是一个专业的视频内容总结助手。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"[-] AI调用失败: {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"[-] AI调用异常: {e}", file=sys.stderr)
    return None

def process_bv(bvid):
    """处理单个BV号"""
    # 获取视频信息
    video_info = get_video_info(bvid)
    if not video_info:
        return None
    
    # 构建内容
    content = video_info['title'] + '\n' + video_info['description']
    
    # 生成总结
    summary = generate_summary(content, video_info['title'])
    
    return {
        'bvid': bvid,
        'title': video_info['title'],
        'content': summary or content
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python simple_bv_summarizer.py BV号")
        sys.exit(1)
    
    bvid = sys.argv[1]
    result = process_bv(bvid)
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("[-] 处理失败", file=sys.stderr)
        sys.exit(1)
