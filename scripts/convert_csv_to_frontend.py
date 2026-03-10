#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将CSV文件中的BV号总结转换为前端需要的JSON格式
"""

import csv
import json
import re
from datetime import datetime
import os

# 文件路径
INPUT_CSV = os.path.join(os.path.dirname(__file__), 'space_merged_with_summary.csv')
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), '..', 'packages', 'web', 'public', 'data', 'csv_top10_summaries.json')

def parse_views(views_str):
    """解析播放量字符串"""
    if '万' in views_str:
        return int(float(views_str.replace('万', '')) * 10000)
    else:
        return int(views_str.replace(',', ''))

def parse_duration(duration_str):
    """解析时长字符串"""
    # 匹配格式如 "11:08", "33:08:00", "1:42:19"
    parts = duration_str.split(':')
    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    else:
        return 0

def main():
    print("开始转换CSV到JSON...")
    
    summaries = []
    current_time = datetime.now().isoformat()
    
    # 尝试不同的编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
    for encoding in encodings:
        try:
            with open(INPUT_CSV, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, 1):
                    
                    bvid = row.get('bvid', '')
                    title = row.get('title', '')
                    views_str = row.get('views', '0')
                    duration_str = row.get('duration', '0:00')
                    summary = row.get('summary', '')
                    
                    # 解析数据
                    view_count = parse_views(views_str)
                    duration = parse_duration(duration_str)
                    
                    # 构建summary对象
                    summary_item = {
                        "rank": i,
                        "bvid": bvid,
                        "title": title,
                        "owner": "大佬何金银",
                        "duration": duration,
                        "view_count": view_count,
                        "summary": summary,
                        "generated_at": current_time
                    }
                    
                    summaries.append(summary_item)
            print(f"成功使用编码 {encoding} 读取CSV文件")
            break
        except Exception as e:
            print(f"使用编码 {encoding} 读取CSV文件失败: {e}")
            continue
    
    if not summaries:
        print("无法读取CSV文件，转换失败！")
        return
    
    # 构建最终JSON结构
    output_data = {
        "generated_at": current_time,
        "total": len(summaries),
        "summaries": summaries
    }
    
    # 保存到文件
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"转换完成！成功生成 {len(summaries)} 个总结")
    print(f"输出文件: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()