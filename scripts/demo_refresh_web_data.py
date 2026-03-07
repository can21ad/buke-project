#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: 用「旧 cookie + BV 列表」抓取少量视频，并刷新前端展示数据。

做了什么：
1) 从 scripts/crawler_v3.py 中解析出你以前写死的 cookie（不在本脚本里硬编码，避免到处散落）。
2) 复用 crawler_v3.py 里的 BilibiliCrawlerV3，按 BV 抓取评论（默认每个 BV 抓 2 页，跑得快）。
3) 生成 scripts/buke_crawler_v3_merged.json（覆盖写入）。
4) 直接把结果转换成 packages/web/public/data/buke_top_stories.json，让网页立刻能看到新数据。

运行：
    cd D:\\怖客\\scripts
    python demo_refresh_web_data.py
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from episode_indexer import EpisodeIndexer, extract_episode_number


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_cookie_from_old_script(old_script_text: str) -> Optional[str]:
    """
    从旧脚本里提取 cookie = "...." 这一段。
    仅用于本地 demo，避免在多个文件里重复写 cookie。
    """
    m = re.search(r'^\s*cookie\s*=\s*"([^"]+)"\s*$', old_script_text, flags=re.MULTILINE)
    if not m:
        return None
    cookie = m.group(1).strip()
    return cookie or None


def _summarize_top_episodes(results: List[Dict[str, Any]], top_n: int = 10) -> List[Tuple[str, int]]:
    """
    汇总所有 result.past_stories 的提及次数，输出 TopN 期数。
    返回：[(story_name, mention_count), ...]  已按次数降序。
    """
    counter: Dict[str, int] = {}
    for result in results:
        for story in result.get("past_stories", []):
            name = str(story.get("name") or "")
            cnt = int(story.get("mention_count") or 0)
            if not name or not cnt:
                continue
            counter[name] = counter.get(name, 0) + cnt
    items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    return items[:top_n]


def _convert_merged_to_frontend(
    merged: Dict[str, Any],
    indexer: EpisodeIndexer,
) -> Dict[str, Any]:
    """
    复用 convert_to_frontend.py 的逻辑，并在此基础上：
    - 对往期故事尝试解析期数并通过空间检索获得对应 BV；
    - 若解析到往期 BV，则将 bvid / jump_url 替换为该 BV；
    - 将“提及排行榜”写入前端数据，便于展示。
    """
    stories: List[Dict[str, Any]] = []
    story_id = 0

    # 统计各期总提及次数
    episode_counter: Dict[str, int] = {}

    for result in merged.get("results", []):
        source_video = result.get("source_video") or ""
        source_bvid = result.get("source_bvid") or ""

        for story in result.get("past_stories", []):
            story_id += 1

            time_markers = story.get("time_markers", []) or []
            timestamp = 0
            if time_markers:
                first_marker = str(time_markers[0])
                parts = first_marker.split(":")
                try:
                    if len(parts) == 2:
                        timestamp = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:
                        timestamp = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                except Exception:
                    timestamp = 0

            comments = story.get("comments", []) or []
            review = comments[0].get("content") if comments and isinstance(comments[0], dict) else story.get("name", "")
            review = str(review or "")

            tags = (story.get("bv_list", []) or [])[:3]
            if not tags:
                tags = ["道听途说", "热门故事"]

            story_name = str(story.get("name") or "")

            # 更新排行榜统计
            total_mentions = int(story.get("mention_count") or 0)
            if story_name and total_mentions:
                episode_counter[story_name] = episode_counter.get(story_name, 0) + total_mentions

            # 默认使用当前 BV；如果是“道听途说XX期”，再尝试映射到对应期数 BV；
            # 如果空间检索失败但评论里有显式 BV 号，则退回到 bv_list[0]
            target_bvid = source_bvid
            target_jump_url = f"https://www.bilibili.com/video/{source_bvid}?t={timestamp}&p=1"

            episode = extract_episode_number(story_name)
            hit = None
            if episode is not None:
                hit = indexer.resolve(episode)
            if hit:
                target_bvid = hit.bvid
                target_jump_url = hit.url
            else:
                bv_list = story.get("bv_list", []) or []
                if bv_list:
                    target_bvid = str(bv_list[0])
                    target_jump_url = f"https://www.bilibili.com/video/{target_bvid}"

            stories.append(
                {
                    "id": story_id,
                    "name": story_name,
                    "title": (source_video[:50] + "...") if len(source_video) > 50 else source_video,
                    "bvid": target_bvid,
                    "timestamp": timestamp,
                    "heat": story.get("heat_score", 0),
                    "mention_count": story.get("mention_count", 0),
                    "review": (review[:500] if len(review) > 500 else review),
                    "length": len(review),
                    "author": "@大佬何金银",
                    "tags": tags[:4],
                    "time_markers": time_markers[:5],
                    "related_bvs": story.get("bv_list", []) or [],
                    "jump_url": target_jump_url,
                }
            )

    stories.sort(key=lambda x: float(x.get("heat") or 0), reverse=True)
    top_stories = stories[:50]

    # 生成“提及排行榜”前 10 名
    episode_rank_raw = sorted(
        episode_counter.items(), key=lambda x: x[1], reverse=True
    )[:10]
    episode_rank = [
        {"name": name, "mention_count": count, "rank": idx + 1}
        for idx, (name, count) in enumerate(episode_rank_raw)
    ]

    return {
        "generated_at": datetime.now().isoformat(),
        "version": "v3.0-demo",
        "total_stories": len(stories),
        "top_n": len(top_stories),
        "theme": "【道听途说系列】热门故事精选（demo刷新）",
        "keywords": ["道听途说", "灵异", "恐怖", "真实经历", "民间传说"],
        "stories": top_stories,
        "episode_rank": episode_rank,
    }


def main() -> None:
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(scripts_dir, ".."))

    old_script_path = os.path.join(scripts_dir, "crawler_v3.py")
    old_text = _read_text(old_script_path)
    cookie = _extract_cookie_from_old_script(old_text)

    # BV 列表：覆盖为更多视频，方便前端展示指向不同 BV 的直达链接
    bvids = [
        "BV1Gg6iB9EbS",  # 三小时特辑
        "BV1D1qpB6ECc",  # 165 上
        "BV19SiFB1E1q",  # 166 下
        "BV1vh3gzwE4H",
        "BV1MLTxz9EZE",
        "BV1xx411c7mD",
        "BV1D1641k7mD",
        "BV1xx411c7mE",
    ]
    pages = int(os.environ.get("DEMO_PAGES", "50"))

    if cookie:
        print("[*] 已从旧脚本解析到 cookie（不会在日志里输出具体内容）")
    else:
        print("[!] 未能从旧脚本解析 cookie，将使用空 cookie 继续尝试")
        cookie = ""

    # 复用旧爬虫类
    from crawler_v3 import BilibiliCrawlerV3  # type: ignore

    all_results: List[Dict[str, Any]] = []
    for bvid in bvids:
        crawler = BilibiliCrawlerV3(cookie=cookie)
        print(f"\n=== 开始抓取 {bvid}（每个视频 {pages} 页评论）===")
        result = crawler.run(bvid, pages=pages)
        if result:
            all_results.append(asdict(result))
        time.sleep(1.5)

    merged = {
        "generated_at": datetime.now().isoformat(),
        "total_videos": len(all_results),
        "results": all_results,
    }

    # 汇总打印 Top 提及期数，方便你核对（例如“145期有25次排第3名”）
    top_episodes = _summarize_top_episodes(all_results, top_n=10)
    if top_episodes:
        print("\n[+] 评论中被提及次数最多的往期故事：")
        for idx, (name, cnt) in enumerate(top_episodes, start=1):
            print(f"  #{idx} {name}  -> 提及 {cnt} 次")

    merged_path = os.path.join(scripts_dir, "buke_crawler_v3_merged.json")
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"\n[+] 已生成 merged：{merged_path}")

    # 使用期数索引器：UP 主 mid = 28346875
    cache_path = os.path.join(scripts_dir, "episode_index.json")
    indexer = EpisodeIndexer(mid=28346875, cache_path=cache_path, headers=None)

    frontend_data = _convert_merged_to_frontend(merged, indexer=indexer)
    out_path = os.path.join(project_root, "packages", "web", "public", "data", "buke_top_stories.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(frontend_data, f, ensure_ascii=False, indent=2)
    print(f"[+] 已刷新前端数据：{out_path}")
    print("[+] 现在可以在 web（packages/web）中查看新的『一键直达』效果了")


if __name__ == "__main__":
    main()

