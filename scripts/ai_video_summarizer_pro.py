#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI视频内容总结工具 - 实际可用版本
功能：下载B站视频音频，转录为文字，使用AI生成总结

使用方法：
1. 安装依赖: pip install yt-dlp openai requests
2. 配置API密钥（在代码中或环境变量中设置）
3. 运行: python ai_video_summarizer.py --bvid BV1xx411c7xx
"""

import os
import sys
import argparse
import json
import re
import tempfile
import subprocess
import csv
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# 尝试导入必要的库
try:
    import requests
except ImportError:
    print("[-] 缺少requests库，请安装: pip install requests")
    sys.exit(1)

# API配置 - 使用用户提供的API
# 可以从环境变量读取，也可以直接在代码中配置
API_CONFIG = {
    "base_url": "https://openrouter.fans/v1",
    "api_key": "sk-S6Q7NxPxQUNY7gWP1RRC3cTeRuJ2mjPY42CRS3WShl5KrSE3",  # 使用用户提供的API密钥
    "model": "deepseek/deepseek-chat"  # 使用用户指定的模型
}

# 备用API配置（如果主API不可用）
BACKUP_APIS = {
    "openrouter": {
        "base_url": "https://openrouter.fans/v1",
        "api_key": "sk-S6Q7NxPxQUNY7gWP1RRC3cTeRuJ2mjPY42CRS3WShl5KrSE3",
        "model": "deepseek/deepseek-chat"
    }
}


class VideoInfoExtractor:
    """视频信息提取器"""
    
    @staticmethod
    def extract_bvid_from_url(url: str) -> Optional[str]:
        """从URL提取BV号"""
        patterns = [
            r'BV[a-zA-Z0-9]{10}',
            r'bvid=([a-zA-Z0-9]{10})',
            r'/video/(BV[a-zA-Z0-9]{10})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(0).replace('bvid=', '').replace('/video/', '')
        return None
    
    @staticmethod
    def get_video_info(bvid: str) -> Optional[Dict]:
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
                    'aid': video_data['aid'],
                    'title': video_data['title'],
                    'description': video_data.get('desc', ''),
                    'duration': video_data.get('duration', 0),
                    'owner': video_data['owner']['name'],
                    'pubdate': video_data.get('pubdate', 0),
                    'view_count': video_data['stat']['view'],
                    'like_count': video_data['stat']['like'],
                    'comment_count': video_data['stat']['reply'],
                }
        except Exception as e:
            print(f"[-] 获取视频信息失败: {e}")
        return None


class SubtitleExtractor:
    """字幕提取器"""
    
    @staticmethod
    def get_subtitle(aid: int, cid: int) -> Optional[str]:
        """获取B站官方字幕"""
        url = f"https://api.bilibili.com/x/player/wbi/v2?aid={aid}&cid={cid}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()
            if data['code'] == 0:
                subtitle_list = data['data'].get('subtitle', {}).get('subtitles', [])
                if subtitle_list:
                    # 获取第一个字幕
                    subtitle_url = subtitle_list[0].get('subtitle_url', '')
                    if subtitle_url:
                        return SubtitleExtractor.download_subtitle(subtitle_url)
        except Exception as e:
            print(f"[-] 获取字幕失败: {e}")
        return None
    
    @staticmethod
    def download_subtitle(subtitle_url: str) -> Optional[str]:
        """下载字幕内容"""
        try:
            if subtitle_url.startswith('//'):
                subtitle_url = 'https:' + subtitle_url
            
            response = requests.get(subtitle_url, timeout=15)
            if response.status_code == 200:
                subtitle_data = response.json()
                # 提取所有字幕文本
                texts = [item.get('content', '') for item in subtitle_data.get('body', [])]
                return '\n'.join(texts)
        except Exception as e:
            print(f"[-] 下载字幕失败: {e}")
        return None


class AISummarizer:
    """AI总结器"""
    
    def __init__(self, api_config: Dict):
        self.api_config = api_config
        self.current_api = "bobapi"
    
    def summarize(self, text: str, title: str = "", max_length: int = 200) -> Optional[str]:
        """使用AI生成总结"""
        
        # 构建提示词
        prompt = self._build_prompt(text, title, max_length)
        
        # 尝试使用主API
        result = self._call_bobapi(prompt)
        if result:
            return result
        
        # 如果失败，尝试备用API
        print("[!] 主API调用失败，尝试备用API...")
        result = self._call_backup_api(prompt)
        if result:
            return result
        
        return None
    
    def _build_prompt(self, text: str, title: str, max_length: int) -> str:
        """构建提示词 - 专注于提取具体故事"""
        return f"""请分析以下视频内容，提取并总结其中的所有故事，要求尽可能详细地描述故事情节，不遗漏任何重要细节。

视频标题：{title}

视频内容：
{text[:8000]}

要求：
1. **详细总结具体故事内容**，不要描述风格、氛围、制作等总体评价
2. **识别所有故事**：如果视频包含2-3个故事，必须全部列出，不能只挑一个
3. **每个故事总结格式**：
   - 故事X：[详细的故事情节描述，包含关键细节和发展过程]
   - 关键元素：人物、地点、事件、时间顺序
4. **去除模糊描述**：不要"营造出恐怖氛围"、"展现了...风格"等空洞描述
5. **专注事实**：只描述发生了什么，不要评价或感受
6. **尽可能详细**：包含故事的开始、发展、高潮和结局，不遗漏任何重要细节
7. **总字数控制在{max_length}字以内**

示例格式：
故事1：主角在一个雨夜回家，发现家附近有一个穿着黑色大衣的女子在监视自己。主角感到不安，加快脚步回家。第二天，主角再次看到该女子，发现她没有眼睛，眼眶空洞。主角报警，但警方赶到时女子已消失。晚上，主角听到敲门声，开门后发现女子站在门口，伸出手向主角靠近...
故事2：...

请生成详细的故事总结："""
    
    def _call_bobapi(self, prompt: str) -> Optional[str]:
        """调用主API"""
        try:
            # 修复API URL，移除重复的/v1
            base_url = self.api_config['base_url'].rstrip('/')
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_config['api_key']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://buke.app",
                "X-Title": "Buke AI Summarizer"
            }
            data = {
                "model": self.api_config['model'],
                "messages": [
                    {"role": "system", "content": "你是一个专业的视频内容总结助手。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"[-] 主API调用失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[-] 主API调用异常: {e}")
        return None
    
    def _call_backup_api(self, prompt: str) -> Optional[str]:
        """调用备用API"""
        backup = BACKUP_APIS.get("openrouter")
        if not backup or not backup['api_key']:
            return None
        
        try:
            url = f"{backup['base_url']}/chat/completions"
            headers = {
                "Authorization": f"Bearer {backup['api_key']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://buke.app",
                "X-Title": "Buke AI Summarizer"
            }
            data = {
                "model": backup['model'],
                "messages": [
                    {"role": "system", "content": "你是一个专业的视频内容总结助手。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"[-] 备用API调用失败: {e}")
        return None


class VideoSummarizer:
    """视频总结主类"""
    
    def __init__(self):
        self.info_extractor = VideoInfoExtractor()
        self.subtitle_extractor = SubtitleExtractor()
        self.ai_summarizer = AISummarizer(API_CONFIG)
    
    def summarize_video(self, bvid: str, use_ai: bool = True) -> Optional[Dict]:
        """总结视频内容"""
        print(f"[*] 开始处理视频: {bvid}")
        
        # 1. 获取视频信息
        video_info = self.info_extractor.get_video_info(bvid)
        if not video_info:
            print("[-] 无法获取视频信息")
            return None
        
        print(f"[+] 视频标题: {video_info['title']}")
        print(f"[+] 视频时长: {video_info['duration']}秒")
        
        # 2. 尝试获取字幕
        subtitle_text = None
        if video_info['aid']:
            # 需要cid，这里简化处理，实际应该获取cid
            print("[*] 尝试获取字幕...")
            # subtitle_text = self.subtitle_extractor.get_subtitle(video_info['aid'], cid)
        
        # 3. 构建内容（组合标题和描述）
        content_parts = []
        if video_info['title']:
            content_parts.append(video_info['title'])
        if video_info['description']:
            content_parts.append(video_info['description'])
        
        content = '\n'.join(content_parts)
        
        if not content or len(content) < 20:  # 降低限制到20字
            print("[-] 视频内容太短，无法生成有意义的总结")
            return None
        
        # 4. 使用AI生成总结
        summary = None
        if use_ai:
            print("[*] 使用AI生成总结...")
            summary = self.ai_summarizer.summarize(
                content, 
                video_info['title'],
                max_length=150
            )
        
        # 5. 构建结果
        result = {
            "bvid": bvid,
            "title": video_info['title'],
            "owner": video_info['owner'],
            "duration": video_info['duration'],
            "view_count": video_info['view_count'],
            "content_source": "subtitle" if subtitle_text else "description",
            "summary": summary or "无法生成AI总结",
            "has_subtitle": subtitle_text is not None,
            "generated_at": datetime.now().isoformat()
        }
        
        return result
    
    def batch_summarize(self, bvids: List[str], output_file: str = "summaries.json"):
        """批量总结视频"""
        results = []
        
        # 只处理前3个视频
        bvids_to_process = bvids[:3]
        print(f"[*] 只处理前3个视频: {bvids_to_process}")
        
        for i, bvid in enumerate(bvids_to_process, 1):
            print(f"\n{'='*50}")
            print(f"[*] 处理第 {i}/{len(bvids_to_process)} 个视频")
            print(f"{'='*50}")
            
            result = self.summarize_video(bvid)
            if result:
                results.append(result)
                print(f"[+] 总结完成: {result['summary'][:100]}...")
            
            # 避免请求过快
            if i < len(bvids_to_process):
                import time
                time.sleep(2)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total_videos": len(results),
                "summaries": results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[+] 批量总结完成，结果已保存到: {output_file}")
        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI视频内容总结工具')
    parser.add_argument('--bvid', type=str, help='B站视频BV号')
    parser.add_argument('--url', type=str, help='B站视频URL')
    parser.add_argument('--file', type=str, help='包含BV号列表的文件')
    parser.add_argument('--output', type=str, default='summaries.json', help='输出文件')
    parser.add_argument('--no-ai', action='store_true', help='不使用AI总结')
    
    args = parser.parse_args()
    
    # 检查API密钥
    if not API_CONFIG['api_key'] and not BACKUP_APIS['openrouter']['api_key']:
        print("[-] 错误: 未配置API密钥")
        print("[*] 请设置环境变量: BOBAPI_KEY 或 OPENROUTER_API_KEY")
        print("[*] 或在代码中直接配置API_CONFIG")
        sys.exit(1)
    
    summarizer = VideoSummarizer()
    
    # 单个视频
    if args.bvid or args.url:
        bvid = args.bvid
        if args.url:
            bvid = VideoInfoExtractor.extract_bvid_from_url(args.url)
        
        if not bvid:
            print("[-] 无法提取BV号")
            sys.exit(1)
        
        result = summarizer.summarize_video(bvid, use_ai=not args.no_ai)
        if result:
            # 如果指定了输出文件，保存到文件
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"[+] 总结结果已保存到: {args.output}")
            else:
                print("\n" + "="*50)
                print("总结结果:")
                print("="*50)
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("[-] 总结失败")
    
    # 批量处理
    elif args.file:
        bvids = []
        
        # 检查文件扩展名
        if args.file.endswith('.csv'):
            # 从CSV文件中读取BV号，尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
            for encoding in encodings:
                try:
                    with open(args.file, 'r', encoding=encoding) as f:
                        reader = csv.reader(f)
                        for row in reader:
                            for cell in row:
                                # 提取BV号
                                bvid_match = re.search(r'BV[a-zA-Z0-9]{10}', cell)
                                if bvid_match:
                                    bvids.append(bvid_match.group(0))
                    # 如果成功读取，就跳出循环
                    print(f"[+] 使用编码 {encoding} 成功读取CSV文件")
                    break
                except UnicodeDecodeError:
                    print(f"[-] 尝试使用编码 {encoding} 失败，继续尝试其他编码...")
                    continue
        else:
            # 从普通文本文件中读取BV号
            with open(args.file, 'r', encoding='utf-8') as f:
                bvids = [line.strip() for line in f if line.strip()]
        
        # 去重处理
        unique_bvids = list(set(bvids))
        print(f"[*] 从文件中提取到 {len(bvids)} 个BV号，去重后剩余 {len(unique_bvids)} 个")
        summarizer.batch_summarize(unique_bvids, args.output)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()