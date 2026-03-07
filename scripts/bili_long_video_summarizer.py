#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 Whisper + LLM 的 B 站长视频 AI 总结脚本（按时间戳拆故事）。

使用场景：
- 只需要：B 站 BV 号 + 你的登录 Cookie（保证能看视频）
- 自动完成：
  1）用 yt-dlp 下载指定 BV 的音频；
  2）用 faster-whisper 转写，保留起止时间戳；
  3）把整段转写交给 LLM，总结为多个「故事」，每个故事有：
     - index：序号
     - start / end：起止时间（秒）
     - title：故事标题
     - summary：详细中文总结
     - keywords：关键词列表
  4）结构化写入 JSON 文件，方便前端 / 其他脚本继续用。

依赖安装（建议在虚拟环境中）：
    pip install yt-dlp faster-whisper openai tiktoken

环境变量：
    OPENAI_API_KEY  ：你的 OpenAI API Key（或改成你自己的 LLM SDK）
    BILIBILI_COOKIE ：你的 B 站 Cookie 字符串（用于 yt-dlp 访问）
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from faster_whisper import WhisperModel
import openai


# ==================== 配置区 ====================

# 默认使用的 Whisper 模型大小（可根据显卡/性能改成 "small" / "medium" / "large-v2"）
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")

# LLM 模型名称（你可以改成 gpt-4.1 / gpt-4.1-mini / 你自己的模型）
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")


# ==================== 数据结构 ====================

@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class StorySummary:
    index: int
    start: float
    end: float
    title: str
    summary: str
    keywords: List[str]


# ==================== 工具函数 ====================

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"环境变量 {name} 未设置，请先在系统/终端中配置后再运行。")
    return value


def download_audio_for_bv(bvid: str, out_dir: str = "downloads") -> str:
    """
    使用 yt-dlp 下载 B 站视频的音频轨，输出为 m4a 文件。
    需要系统已安装 ffmpeg。
    """
    cookie = require_env("BILIBILI_COOKIE")

    os.makedirs(out_dir, exist_ok=True)
    url = f"https://www.bilibili.com/video/{bvid}"
    # 注意：yt-dlp 的 -o 是模板，这里固定文件名，避免生成额外扩展
    out_path = os.path.join(out_dir, f"{bvid}.m4a")

    # 把 cookie 写到临时文件，避免命令行太长
    cookie_file = os.path.join(out_dir, "bilibili_cookie.txt")
    with open(cookie_file, "w", encoding="utf-8") as f:
        f.write(cookie)

    cmd = [
        "yt-dlp",
        "--cookies", cookie_file,
        "-f",
        "ba",  # best audio
        "-x",
        "--audio-format",
        "m4a",
        "-o",
        out_path,
        url,
    ]

    print(f"[*] 正在下载音频：{url}")
    subprocess.run(cmd, check=True)
    print(f"[+] 音频已保存：{out_path}")
    return out_path


def transcribe_audio(audio_path: str) -> List[Segment]:
    """
    使用 faster-whisper 转写音频，返回带时间戳的分段列表。
    """
    print(f"[*] 正在加载 Whisper 模型：{WHISPER_MODEL_SIZE}")
    # device 自动选择 GPU / CPU
    device = "cuda" if os.environ.get("WHISPER_DEVICE", "auto") == "cuda" else "cpu"
    model = WhisperModel(WHISPER_MODEL_SIZE, device=device)

    print(f"[*] 开始转写：{audio_path}")
    segments_iter, _ = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        language="zh",
    )

    segments: List[Segment] = []
    for seg in segments_iter:
        segments.append(
            Segment(
                start=float(seg.start or 0.0),
                end=float(seg.end or 0.0),
                text=(seg.text or "").strip(),
            )
        )

    print(f"[+] 转写完成，共 {len(segments)} 段")
    return segments


def build_transcript_with_timestamps(segments: List[Segment]) -> str:
    """
    把 Segment 列表拼成带时间戳的长文本，提供给 LLM 使用。
    格式： [start-end] 文本
    时间使用秒，LLM 更好解析。
    """
    lines = []
    for s in segments:
        lines.append(f"[{s.start:.1f}-{s.end:.1f}] {s.text}")
    return "\n".join(lines)


def call_llm_for_stories(transcript: str, episode_name: str, bvid: str) -> List[StorySummary]:
    """
    调用 LLM，对整段逐字稿做「按时间切分故事」总结。
    """
    openai.api_key = require_env("OPENAI_API_KEY")

    system_prompt = (
        "你是一个擅长梳理长篇叙事视频的中文编辑，"
        "会根据时间戳把视频划分成若干个清晰的故事段落，并输出结构化结果。"
    )

    user_prompt = f"""
下面是 B 站视频《{episode_name}》（BV 号：{bvid}）的完整逐字稿，格式为：
[开始时间-结束时间] 文本
时间单位为秒。

请你：
1. 按时间顺序，把视频自动划分成若干「故事/段落」，每个故事的时间范围不能交叉，且覆盖视频中绝大多数有内容的时间。
2. 对每个故事，输出：
   - index：从 1 开始递增的序号
   - start：故事开始时间（秒，取该故事第一个句子的开始时间）
   - end：故事结束时间（秒，取该故事最后一个句子的结束时间）
   - title：一个简短、有记忆点的中文标题
   - summary：对该故事的详细中文总结，200~400 字，注意保持逻辑完整
   - keywords：3~8 个关键词，全部为中文短语

请严格输出 JSON 对象，格式为：
{{
  "episode": "{episode_name}",
  "bvid": "{bvid}",
  "stories": [
    {{
      "index": 1,
      "start": 0.0,
      "end": 123.4,
      "title": "……",
      "summary": "……",
      "keywords": ["……", "……"]
    }},
    ...
  ]
}}

不要添加注释或多余说明。

逐字稿如下：
{transcript}
"""

    print("[*] 正在调用 LLM 进行故事切分和总结……")
    completion = openai.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        # 如果模型没完全按 JSON 返回，可以提醒用户手动检查
        raise RuntimeError("LLM 返回的内容不是合法 JSON，请检查模型输出。")

    stories: List[StorySummary] = []
    for item in data.get("stories", []):
        stories.append(
            StorySummary(
                index=int(item.get("index", 0)),
                start=float(item.get("start", 0.0)),
                end=float(item.get("end", 0.0)),
                title=str(item.get("title", "")).strip(),
                summary=str(item.get("summary", "")).strip(),
                keywords=list(item.get("keywords", []) or []),
            )
        )

    print(f"[+] LLM 总结完成，共 {len(stories)} 个故事段落")
    return stories


def summarize_bv(episode_name: str, bvid: str, output_dir: str = "summaries") -> str:
    """
    针对单个 BV 执行完整流程，并把结果写成 JSON 文件。
    返回输出文件路径。
    """
    audio_path = download_audio_for_bv(bvid)
    segments = transcribe_audio(audio_path)
    transcript = build_transcript_with_timestamps(segments)
    stories = call_llm_for_stories(transcript, episode_name, bvid)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{bvid}_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "episode": episode_name,
                "bvid": bvid,
                "stories": [asdict(s) for s in stories],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"[+] 已写出总结：{out_path}")
    return out_path


def main() -> None:
    """
    demo：先对 169 上 / 169 下 两期跑一遍。
    你可以按需修改 BV 号和期数名称。
    """
    # 注意：下面 BV 号需要你确认成真正的 169 上 / 169 下 对应 BV
    targets: Dict[str, str] = {
        "道听途说169上": "BV1xx411c7mE",
        "道听途说169下": "BV1xx411c7mD",
    }

    for episode_name, bvid in targets.items():
        try:
            summarize_bv(episode_name, bvid)
        except Exception as e:
            print(f"[!] 处理 {episode_name}（{bvid}）时出错：{e}")


if __name__ == "__main__":
    main()

