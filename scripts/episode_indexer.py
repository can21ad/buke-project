#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期数索引器：把“道听途说145期”映射到 UP 投稿页对应视频 BV/URL。

实现方式：
- 使用 B 站空间检索接口：/x/space/arc/search（mid + keyword）
- 结果用本地 JSON 缓存，避免重复请求触发风控
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import requests


EPISODE_RE = re.compile(r"道听途说\s*(\d+)\s*期")


def extract_episode_number(story_name: str) -> Optional[int]:
    m = EPISODE_RE.search(story_name or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


@dataclass
class EpisodeHit:
    episode: int
    bvid: str
    title: str
    pubdate: int
    url: str
    matched_keyword: str
    updated_at: str


class EpisodeIndexer:
    def __init__(
        self,
        mid: int,
        cache_path: str,
        headers: Optional[Dict[str, str]] = None,
        sleep_s: float = 0.35,
    ) -> None:
        self.mid = int(mid)
        self.cache_path = cache_path
        self.headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
        }
        self.sleep_s = float(sleep_s)
        self._cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _save_cache(self) -> None:
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def get_cached(self, episode: int) -> Optional[EpisodeHit]:
        item = self._cache.get(str(episode))
        if not item:
            return None
        try:
            return EpisodeHit(**item)
        except Exception:
            return None

    def resolve(self, episode: int, force_refresh: bool = False) -> Optional[EpisodeHit]:
        if not force_refresh:
            cached = self.get_cached(episode)
            if cached:
                return cached

        hit = self._resolve_via_space_search(episode)
        if hit:
            self._cache[str(episode)] = asdict(hit)
            self._save_cache()
        return hit

    def _resolve_via_space_search(self, episode: int) -> Optional[EpisodeHit]:
        keywords = [
            f"道听途说{episode}",
            f"第{episode}期",
            f"{episode}期",
        ]
        best: Optional[Tuple[float, Dict[str, Any], str]] = None  # (score, item, keyword)

        for kw in keywords:
            # 拉 1~2 页就够了，避免过多请求
            for pn in (1, 2):
                items = self._space_arc_search(keyword=kw, pn=pn, ps=30)
                if not items:
                    break
                for it in items:
                    score = self._score_candidate(title=str(it.get("title") or ""), episode=episode)
                    if best is None or score > best[0] or (score == best[0] and int(it.get("pubdate") or 0) > int(best[1].get("pubdate") or 0)):
                        best = (score, it, kw)

                time.sleep(self.sleep_s)

            if best and best[0] >= 8:
                # 分数足够高就不再换关键词找了
                break

        if not best:
            return None

        it = best[1]
        bvid = str(it.get("bvid") or "")
        title = str(it.get("title") or "")
        pubdate = int(it.get("pubdate") or 0)
        if not bvid:
            return None

        return EpisodeHit(
            episode=episode,
            bvid=bvid,
            title=title,
            pubdate=pubdate,
            url=f"https://www.bilibili.com/video/{bvid}",
            matched_keyword=best[2],
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        )

    def _space_arc_search(self, keyword: str, pn: int = 1, ps: int = 30) -> List[Dict[str, Any]]:
        url = "https://api.bilibili.com/x/space/arc/search"
        params = {
            "mid": self.mid,
            "keyword": keyword,
            "pn": int(pn),
            "ps": int(ps),
            "order": "pubdate",
        }
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=15)
            data = resp.json()
            if data.get("code") != 0:
                return []
            vlist = (data.get("data") or {}).get("list") or {}
            items = vlist.get("vlist") or []
            if isinstance(items, list):
                return items
        except Exception:
            return []
        return []

    @staticmethod
    def _score_candidate(title: str, episode: int) -> float:
        """
        启发式打分：尽量命中“道听途说{episode}”的正片，排除特辑/合集/剪辑。
        """
        t = title.replace("【", "").replace("】", "").replace(" ", "")
        score = 0.0

        if f"道听途说{episode}" in t:
            score += 10
        if f"第{episode}期" in t or f"{episode}期" in t:
            score += 4

        # 上/下是正片常见形式
        if "上" in t or "下" in t:
            score += 0.5

        # 负面关键词
        for bad in ("特辑", "合集", "剪辑", "混剪", "盘点", "回顾"):
            if bad in t:
                score -= 6

        # 过短标题通常不是正片
        if len(t) < 8:
            score -= 2

        return score

