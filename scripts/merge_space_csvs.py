#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合 C:\\Users\\can\\Downloads 目录下的所有 space*.csv，
合并为一份去重后的「视频索引数据库」，并顺便下载封面图。

输入 CSV（示例）字段：
  "bili-cover-card href",
  "b-img__inner src",
  "bili-cover-card__stat",
  "bili-cover-card__stat 2",
  "bili-cover-card__stat 3",
  "bili-video-card__title",
  "bili-video-card__subtitle"

输出：
  1) scripts/space_merged.csv
  2) packages/web/public/data/buke_all_episodes.json  （可作为网站数据库）
  3) packages/web/public/covers/{bvid}.jpg           （本地封面图，若下载成功）
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Dict

import requests


DOWNLOADS_DIR = r"C:\Users\can\Downloads"
CSV_PATTERN_PREFIX = "space"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "packages", "web", "public")

MERGED_CSV_PATH = os.path.join(SCRIPTS_DIR, "space_merged.csv")
MERGED_JSON_PATH = os.path.join(PUBLIC_DIR, "data", "buke_all_episodes.json")
COVERS_DIR = os.path.join(PUBLIC_DIR, "covers")

BVID_RE = re.compile(r"/video/(BV[0-9A-Za-z]+)")


@dataclass
class VideoRecord:
    bvid: str
    title: str
    video_url: str
    cover_url: str
    views: str
    stat2: str
    duration: str
    date: str
    local_cover: str


def find_csv_files() -> List[str]:
    files = []
    for name in os.listdir(DOWNLOADS_DIR):
        if not name.lower().endswith(".csv"):
            continue
        if not name.startswith(CSV_PATTERN_PREFIX):
            continue
        files.append(os.path.join(DOWNLOADS_DIR, name))
    files.sort()
    return files


def extract_bvid(url: str) -> str:
    m = BVID_RE.search(url)
    return m.group(1) if m else ""


def read_one_csv(path: str) -> List[VideoRecord]:
    records: List[VideoRecord] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            href = row.get("bili-cover-card href", "").strip().strip('"')
            cover = row.get("b-img__inner src", "").strip().strip('"')
            stat1 = row.get("bili-cover-card__stat", "").strip().strip('"')
            stat2 = row.get("bili-cover-card__stat 2", "").strip().strip('"')
            stat3 = row.get("bili-cover-card__stat 3", "").strip().strip('"')
            title = row.get("bili-video-card__title", "").strip().strip('"')
            subtitle = row.get("bili-video-card__subtitle", "").strip().strip('"')

            bvid = extract_bvid(href)
            if not bvid:
                continue

            # 有的 CSV 把日期放在 subtitle
            date = subtitle
            rec = VideoRecord(
                bvid=bvid,
                title=title,
                video_url=href,
                cover_url=cover,
                views=stat1,
                stat2=stat2,
                duration=stat3,
                date=date,
                local_cover="",  # 稍后填
            )
            records.append(rec)
    return records


def download_cover(rec: VideoRecord) -> str:
    """
    下载封面图到 covers 目录，文件名使用 {bvid}.jpg。
    若失败则返回空字符串。
    """
    if not rec.cover_url:
        return ""

    os.makedirs(COVERS_DIR, exist_ok=True)
    # 去掉 @ 后面的尺寸/格式参数
    url = rec.cover_url.split("@", 1)[0]
    ext = ".jpg"
    if "." in url.split("/")[-1]:
        ext = "." + url.split("/")[-1].split(".")[-1]
    filename = rec.bvid + ext
    out_path = os.path.join(COVERS_DIR, filename)

    if os.path.exists(out_path):
        return "/covers/" + filename

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return "/covers/" + filename
    except Exception as e:
        print(f"[!] 下载封面失败 {rec.bvid}: {e}")
        return ""


def merge_all() -> List[VideoRecord]:
    csv_files = find_csv_files()
    print(f"[*] 在 {DOWNLOADS_DIR} 找到 {len(csv_files)} 个 CSV：")
    for p in csv_files:
        print("   -", os.path.basename(p))

    merged: Dict[str, VideoRecord] = {}
    for path in csv_files:
        recs = read_one_csv(path)
        print(f"[+] 读取 {os.path.basename(path)} -> {len(recs)} 条")
        for r in recs:
            # 按 bvid 去重，保留最新一次看到的记录
            merged[r.bvid] = r

    print(f"[+] 合并后共 {len(merged)} 条视频记录")

    # 下载封面
    for r in merged.values():
        r.local_cover = download_cover(r) or ""

    return sorted(merged.values(), key=lambda x: x.bvid)


def write_outputs(records: List[VideoRecord]) -> None:
    os.makedirs(os.path.dirname(MERGED_CSV_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(MERGED_JSON_PATH), exist_ok=True)

    # 写 CSV
    with open(MERGED_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "bvid",
                "title",
                "video_url",
                "cover_url",
                "local_cover",
                "views",
                "stat2",
                "duration",
                "date",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.bvid,
                    r.title,
                    r.video_url,
                    r.cover_url,
                    r.local_cover,
                    r.views,
                    r.stat2,
                    r.duration,
                    r.date,
                ]
            )
    print(f"[+] 已写入合并 CSV：{MERGED_CSV_PATH}")

    # 写 JSON
    data = [asdict(r) for r in records]
    with open(MERGED_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": __import__("datetime").datetime.now().isoformat(),
                "total": len(records),
                "videos": data,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[+] 已写入网站数据库 JSON：{MERGED_JSON_PATH}")


def main() -> None:
    records = merge_all()
    write_outputs(records)
    print("[✓] 所有 CSV 已整合完毕，可作为网站数据库使用。")


if __name__ == "__main__":
    main()

