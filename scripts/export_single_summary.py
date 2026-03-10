#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据指定 BV 号生成单个视频的总结 JSON（UTF-8），方便手动查看或前端调试。

使用方式：
    cd D:\怖客\scripts
    python export_single_summary.py BV1464y1Y71A
"""

import json
import sys
from pathlib import Path

from ai_video_summarizer_pro import VideoSummarizer


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python export_single_summary.py <BV号>")
        sys.exit(1)

    bvid = sys.argv[1].strip()
    summarizer = VideoSummarizer()
    result = summarizer.summarize_video(bvid)
    if not result:
        print("生成总结失败：无法获取视频信息或 AI 总结失败")
        sys.exit(1)

    out_name = f"summary_{bvid}.json"
    out_path = Path(out_name)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已写入 UTF-8 JSON 文件：{out_path.resolve()}")


if __name__ == "__main__":
    main()

