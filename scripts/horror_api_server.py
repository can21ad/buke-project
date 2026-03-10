#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易后端服务：结合 B 站 BV 总结脚本 + 恐怖度打分 API

用途：
- 提供两个 HTTP 接口给前端页面调用：
  1) GET  /api/v1/analyze-from-bv/{bvid}
     - 输入：B 站 BV 号
     - 流程：调用 VideoSummarizer 生成故事总结 -> 调用 AI 做恐怖度打分
     - 输出：{ summary, scores: {overall, atmosphere, psychological, gore}, reason }
  2) POST /api/v1/analyze-story
     - 输入：JSON { "story": "故事正文" }
     - 流程：直接对故事做恐怖度打分
     - 输出格式同上

运行方式（建议在 D:\\怖客\\scripts 目录下）：
    pip install fastapi uvicorn requests
    python horror_api_server.py

服务默认监听：http://127.0.0.1:8000
"""

from __future__ import annotations

import json
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_video_summarizer_pro import VideoSummarizer


app = FastAPI(title="Buke Horror Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


OPENROUTER_API_KEY = "sk-S6Q7NxPxQUNY7gWP1RRC3cTeRuJ2mjPY42CRS3WShl5KrSE3"
OPENROUTER_BASE_URL = "https://openrouter.fans/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat"


def call_horror_scoring_model(story: str) -> Dict[str, Any]:
    """调用 AI 对故事做恐怖度打分，返回标准结构。"""
    if not story or len(story.strip()) < 10:
        raise HTTPException(status_code=400, detail="故事内容过短，无法分析")

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "你是一个恐怖文学品鉴专家。请阅读用户提交的故事，并严格只返回 JSON：\n"
        "{\n"
        '  "summary": "50字以内的故事总结",\n'
        '  "scores": {\n'
        '    "atmosphere": 1 到 5 的整数,\n'
        '    "psychological": 1 到 5 的整数,\n'
        '    "gore": 1 到 5 的整数,\n'
        '    "overall": 1 到 5 的整数\n'
        "  },\n"
        '  "reason": "一句话解释为什么给这个分数"\n'
        "}\n"
        "不要输出任何解释文字，不要包裹代码块标记。"
    )
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": story},
        ],
        "temperature": 0.7,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:  # 网络错误
        raise HTTPException(status_code=502, detail=f"调用评分模型失败: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"评分模型返回异常: {resp.status_code} - {resp.text}",
        )

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        raise HTTPException(status_code=502, detail="评分模型返回格式不正确")

    # 尝试把 content 解析成 JSON
    try:
        result = json.loads(content)
    except Exception:
        # 如果解析失败，简单兜底，避免前端完全报错
        return {
            "summary": story[:50] + "..." if len(story) > 50 else story,
            "scores": {
                "atmosphere": 3,
                "psychological": 3,
                "gore": 2,
                "overall": 3,
            },
            "reason": "AI 返回格式异常，使用默认中等恐怖度作为兜底结果。",
        }

    # 兜底补全字段，避免前端因为缺字段报错
    scores = result.get("scores") or {}
    return {
        "summary": result.get("summary", story[:50]),
        "scores": {
            "atmosphere": int(scores.get("atmosphere", 3)),
            "psychological": int(scores.get("psychological", 3)),
            "gore": int(scores.get("gore", 2)),
            "overall": int(scores.get("overall", 3)),
        },
        "reason": result.get("reason", "AI 分析完成。"),
    }


@app.get("/api/v1/analyze-from-bv/{bvid}")
def analyze_from_bv(bvid: str) -> Dict[str, Any]:
    """前端传 BV 号，后端：总结 + 恐怖度打分，一次性返回。"""
    summarizer = VideoSummarizer()
    result = summarizer.summarize_video(bvid)
    if not result:
        raise HTTPException(status_code=404, detail="无法获取视频信息或生成总结")

    story_summary = result.get("summary") or ""
    scoring = call_horror_scoring_model(story_summary)

    return {
        "code": 200,
        "data": {
            "bvid": bvid,
            "title": result.get("title"),
            "owner": result.get("owner"),
            "summary": scoring["summary"],
            "scores": scoring["scores"],
            "reason": scoring["reason"],
            "raw_summary": story_summary,
        },
    }


@app.post("/api/v1/analyze-story")
def analyze_story(body: Dict[str, Any]) -> Dict[str, Any]:
    """直接对用户提交的故事文本做恐怖度打分。"""
    story = (body.get("story") or "").strip()
    if not story:
        raise HTTPException(status_code=400, detail="story 字段不能为空")

    scoring = call_horror_scoring_model(story)
    return {
        "code": 200,
        "data": scoring,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

