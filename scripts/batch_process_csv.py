#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理CSV文件中的BV号，使用ai_video_summarizer_pro.py生成总结，并将结果添加到CSV文件中
"""

import os
import sys
import csv
import json
import subprocess
import time
from datetime import datetime

# 脚本路径
SUMMARIZER_SCRIPT = os.path.join(os.path.dirname(__file__), 'ai_video_summarizer_pro.py')
INPUT_CSV = os.path.join(os.path.dirname(__file__), 'space_merged.csv')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), 'space_merged_with_summary_first50.csv')

# 日志文件
LOG_FILE = os.path.join(os.path.dirname(__file__), 'batch_process_log.txt')

# 结果缓存文件
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'summary_cache.json')

# 加载缓存
cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"[+] 加载缓存，已处理 {len(cache)} 个BV号")
    except Exception as e:
        print(f"[-] 加载缓存失败: {e}")

# 日志函数
def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

# 运行总结脚本
def run_summarizer(bvid):
    # 检查缓存
    if bvid in cache:
        log(f"[+] 从缓存中获取 {bvid} 的总结")
        return cache[bvid]
    
    log(f"[*] 处理BV号: {bvid}")
    
    # 运行脚本
    cmd = f'python "{SUMMARIZER_SCRIPT}" --bvid {bvid} --output temp_summary.json'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # 读取结果
            with open('temp_summary.json', 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            # 提取总结
            summary = summary_data.get('summary', '无法生成总结')
            
            # 保存到缓存
            cache[bvid] = summary
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            
            # 清理临时文件
            if os.path.exists('temp_summary.json'):
                os.remove('temp_summary.json')
            
            log(f"[+] 成功处理 {bvid}")
            return summary
        else:
            log(f"[-] 处理 {bvid} 失败: {result.stderr}")
            return "处理失败"
    except Exception as e:
        log(f"[-] 处理 {bvid} 异常: {e}")
        return "处理异常"

# 主函数
def main():
    log("开始批量处理CSV文件中的BV号")
    
    # 读取CSV文件
    rows = []
    encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
    header = []
    
    for encoding in encodings:
        try:
            with open(INPUT_CSV, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                header = next(reader)  # 读取表头
                for row in reader:
                    rows.append(row)
            log(f"[+] 使用编码 {encoding} 成功读取CSV文件，共 {len(rows)} 行")
            break
        except Exception as e:
            log(f"[-] 使用编码 {encoding} 读取CSV文件失败: {e}")
            rows = []
            continue
    
    if not header:
        log("[-] 无法读取CSV文件")
        sys.exit(1)
    
    # 添加总结列到表头
    header.append('summary')
    
    # 检查是否存在已处理的文件
    existing_summaries = {}
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                existing_header = next(reader)
                if 'summary' in existing_header:
                    for row in reader:
                        if len(row) > 1:
                            existing_summaries[row[0]] = row[1]
            log(f"[+] 加载已处理的总结，共 {len(existing_summaries)} 个")
        except Exception as e:
            log(f"[-] 加载已处理文件失败: {e}")
    
    # 处理每一行
    processed_rows = [header]
    processed_count = 0
    max_process = 50  # 处理前50个BV号
    start_row = 1  # 从第1行开始处理
    
    for i, row in enumerate(rows, 1):
        bvid = row[0]
        
        # 检查是否已经处理过
        if bvid in existing_summaries:
            # 保留之前的总结
            row.append(existing_summaries[bvid])
            processed_rows.append(row)
            log(f"[+] 保留 {bvid} 的已有总结")
        else:
            # 从指定行开始处理
            if i >= start_row and processed_count < max_process:
                log(f"[*] 处理第 {i}/{len(rows)} 行: {bvid}")
                
                # 运行总结脚本
                summary = run_summarizer(bvid)
                
                # 添加总结到行
                row.append(summary)
                processed_rows.append(row)
                processed_count += 1
                
                # 保存中间结果
                if processed_count % 10 == 0:
                    try:
                        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerows(processed_rows)
                        log(f"[+] 已保存 {processed_count} 个新总结")
                    except Exception as e:
                        log(f"[-] 保存中间结果失败: {e}")
                
                # 避免请求过快
                time.sleep(2)
            else:
                # 未处理的行，添加空总结
                row.append('')
                processed_rows.append(row)
    
    log(f"[+] 本次处理了 {processed_count} 个新BV号")
    
    # 保存最终结果
    try:
        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(processed_rows)
        log(f"[+] 成功保存结果到 {OUTPUT_CSV}")
    except Exception as e:
        log(f"[-] 保存结果失败: {e}")
        sys.exit(1)
    
    log("批量处理完成")

if __name__ == "__main__":
    main()
