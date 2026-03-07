#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能视频内容总结脚本
功能：将视频文件转换为文本并生成智能总结
依赖：AssemblyAI（语音转文字）和OpenAI（文本总结）
"""

import os
import argparse
import requests
import json
from openai import OpenAI

# 配置API密钥（请替换为您自己的API密钥）
ASSEMBLYAI_API_KEY = "YOUR_ASSEMBLYAI_API_KEY"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# 初始化OpenAI客户端
client = OpenAI(api_key=OPENAI_API_KEY)

def upload_video_to_assemblyai(video_path):
    """上传视频到AssemblyAI并获取上传URL"""
    print("正在上传视频文件...")
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
    }
    with open(video_path, "rb") as f:
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f
        )
    upload_url = response.json()["upload_url"]
    print(f"视频上传成功，URL: {upload_url}")
    return upload_url

def transcribe_video(upload_url):
    """使用AssemblyAI转录视频内容"""
    print("正在转录视频内容...")
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "audio_url": upload_url,
        "language_code": "zh",  # 设置为中文
        "speaker_labels": True  # 启用说话人识别
    }
    response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json=data
    )
    transcript_id = response.json()["id"]
    print(f"转录任务已创建，ID: {transcript_id}")
    
    # 轮询转录状态
    while True:
        response = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers
        )
        status = response.json()["status"]
        if status == "completed":
            print("转录完成！")
            return response.json()
        elif status == "failed":
            print("转录失败！")
            return None
        else:
            print("转录中...")
            import time
            time.sleep(5)

def generate_summary(transcript_text):
    """使用OpenAI生成视频内容总结"""
    print("正在生成视频内容总结...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的视频内容总结助手，能够从视频转录文本中提取关键信息，生成简洁明了的总结。"
                },
                {
                    "role": "user",
                    "content": f"请对以下视频转录内容进行总结，提取主要观点和关键信息，保持语言流畅自然：\n{transcript_text}"
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        summary = response.choices[0].message.content
        print("总结生成完成！")
        return summary
    except Exception as e:
        print(f"生成总结时出错: {e}")
        return None

def main(video_path, output_file=None):
    """主函数"""
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        return
    
    # 1. 上传视频
    upload_url = upload_video_to_assemblyai(video_path)
    
    # 2. 转录视频
    transcript = transcribe_video(upload_url)
    if not transcript:
        print("转录失败，无法继续")
        return
    
    transcript_text = transcript.get("text", "")
    if not transcript_text:
        print("转录文本为空，无法生成总结")
        return
    
    # 3. 生成总结
    summary = generate_summary(transcript_text)
    if not summary:
        print("生成总结失败")
        return
    
    # 4. 输出结果
    print("\n=== 视频内容总结 ===")
    print(summary)
    
    # 5. 保存结果到文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=== 视频内容总结 ===\n")
            f.write(summary)
            f.write("\n\n=== 完整转录文本 ===\n")
            f.write(transcript_text)
        print(f"\n结果已保存到: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI智能视频内容总结脚本")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    args = parser.parse_args()
    
    main(args.video_path, args.output)
