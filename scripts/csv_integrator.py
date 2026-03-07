#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - CSV数据整合脚本
==========================================
整合Downloads目录下的CSV文件，统一字段名称，下载封面图片
"""

import os
import sys
import csv
import json
import re
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from urllib.parse import urlparse


class CSVDataIntegrator:
    """CSV数据整合器"""
    
    # 标准字段名称映射
    FIELD_MAPPING = {
        'bili-cover-card href': 'video_url',
        'b-img__inner src': 'cover_url',
        'bili-cover-card__stat': 'play_count',
        'bili-cover-card__stat 2': 'comment_count',
        'bili-cover-card__stat 3': 'duration',
        'bili-video-card__title': 'title',
        'bili-video-card__subtitle': 'upload_date',
    }
    
    # 标准字段顺序
    STANDARD_FIELDS = [
        'id', 'bvid', 'video_url', 'cover_url', 'cover_local', 
        'play_count', 'comment_count', 'duration', 'title', 
        'upload_date', 'episode', 'part'
    ]
    
    def __init__(self, download_dir: str, output_dir: str):
        self.download_dir = download_dir
        self.output_dir = output_dir
        self.covers_dir = os.path.join(output_dir, 'covers')
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.covers_dir, exist_ok=True)
        
        self.all_data = []
        self.cover_mapping = {}
        self.stats = {
            'total_files': 0,
            'total_records': 0,
            'total_covers': 0,
            'failed_covers': 0,
        }
    
    def find_csv_files(self) -> List[str]:
        """查找所有CSV文件"""
        csv_files = []
        for f in os.listdir(self.download_dir):
            if f.endswith('.csv'):
                csv_files.append(os.path.join(self.download_dir, f))
        
        print(f"[*] 找到 {len(csv_files)} 个CSV文件")
        return csv_files
    
    def extract_bvid(self, url: str) -> str:
        """从URL提取BV号"""
        match = re.search(r'(BV[a-zA-Z0-9]{10})', url)
        return match.group(1) if match else ''
    
    def parse_play_count(self, count_str: str) -> int:
        """解析播放量"""
        if not count_str:
            return 0
        
        count_str = count_str.strip().replace('"', '').replace(',', '')
        
        try:
            if '万' in count_str:
                num = float(count_str.replace('万', ''))
                return int(num * 10000)
            elif '亿' in count_str:
                num = float(count_str.replace('亿', ''))
                return int(num * 100000000)
            else:
                return int(float(count_str))
        except:
            return 0
    
    def parse_duration(self, duration_str: str) -> int:
        """解析时长为秒数"""
        if not duration_str:
            return 0
        
        duration_str = duration_str.strip().replace('"', '')
        
        parts = duration_str.split(':')
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass
        
        return 0
    
    def parse_upload_date(self, date_str: str) -> str:
        """解析上传日期"""
        if not date_str:
            return ''
        
        date_str = date_str.strip().replace('"', '')
        
        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m月%d日',
        ]
        
        for fmt in formats:
            try:
                if '月' in date_str:
                    # 处理 "2月28日" 格式
                    match = re.match(r'(\d+)月(\d+)日', date_str)
                    if match:
                        month, day = match.groups()
                        return f"2026-{int(month):02d}-{int(day):02d}"
            except:
                pass
        
        return date_str
    
    def extract_episode_info(self, title: str) -> Dict:
        """从标题提取期数信息"""
        info = {'episode': 0, 'part': ''}
        
        # 匹配期数，如 "道听途说169下"
        match = re.search(r'道听途说(\d+)([上下])?', title)
        if match:
            info['episode'] = int(match.group(1))
            info['part'] = match.group(2) or ''
        
        return info
    
    def read_csv_file(self, file_path: str) -> List[Dict]:
        """读取单个CSV文件"""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # 映射字段名称
                    record = {}
                    for old_name, new_name in self.FIELD_MAPPING.items():
                        if old_name in row:
                            record[new_name] = row[old_name].strip().strip('"')
                    
                    if record.get('video_url'):
                        records.append(record)
        
        except Exception as e:
            print(f"[-] 读取文件失败 {file_path}: {e}")
        
        return records
    
    def standardize_record(self, record: Dict, record_id: int) -> Dict:
        """标准化单条记录"""
        bvid = self.extract_bvid(record.get('video_url', ''))
        
        episode_info = self.extract_episode_info(record.get('title', ''))
        
        standardized = {
            'id': record_id,
            'bvid': bvid,
            'video_url': record.get('video_url', ''),
            'cover_url': record.get('cover_url', ''),
            'cover_local': '',
            'play_count': self.parse_play_count(record.get('play_count', '0')),
            'comment_count': self.parse_play_count(record.get('comment_count', '0')),
            'duration': self.parse_duration(record.get('duration', '0')),
            'duration_str': record.get('duration', ''),
            'title': record.get('title', ''),
            'upload_date': self.parse_upload_date(record.get('upload_date', '')),
            'episode': episode_info['episode'],
            'part': episode_info['part'],
        }
        
        return standardized
    
    def download_cover(self, cover_url: str, bvid: str) -> Optional[str]:
        """下载封面图片"""
        if not cover_url or not bvid:
            return None
        
        # 清理URL
        cover_url = cover_url.split('@')[0]  # 移除尺寸参数
        
        # 确定文件扩展名
        ext = '.jpg'
        if '.png' in cover_url:
            ext = '.png'
        elif '.avif' in cover_url:
            ext = '.jpg'  # 转换为jpg
        
        local_path = os.path.join(self.covers_dir, f"{bvid}{ext}")
        
        # 如果已存在，直接返回
        if os.path.exists(local_path):
            return f"covers/{bvid}{ext}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
            }
            
            response = requests.get(cover_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                self.stats['total_covers'] += 1
                return f"covers/{bvid}{ext}"
            else:
                self.stats['failed_covers'] += 1
                return None
        
        except Exception as e:
            self.stats['failed_covers'] += 1
            return None
    
    def process_all_files(self):
        """处理所有CSV文件"""
        csv_files = self.find_csv_files()
        
        if not csv_files:
            print("[!] 没有找到CSV文件")
            return
        
        print(f"\n[*] 开始处理CSV文件...")
        
        all_records = []
        record_id = 0
        seen_bvids = set()
        
        for csv_file in csv_files:
            print(f"\n处理: {os.path.basename(csv_file)}")
            
            records = self.read_csv_file(csv_file)
            self.stats['total_files'] += 1
            
            for record in records:
                bvid = self.extract_bvid(record.get('video_url', ''))
                
                # 跳过重复的BV号
                if bvid in seen_bvids:
                    continue
                
                seen_bvids.add(bvid)
                record_id += 1
                
                standardized = self.standardize_record(record, record_id)
                all_records.append(standardized)
                
                # 下载封面
                if standardized['cover_url']:
                    cover_local = self.download_cover(standardized['cover_url'], bvid)
                    standardized['cover_local'] = cover_local or ''
                    
                    # 建立映射关系
                    self.cover_mapping[bvid] = {
                        'cover_url': standardized['cover_url'],
                        'cover_local': cover_local or '',
                    }
                
                print(f"  [{record_id}] {bvid}: {standardized['title'][:30]}...")
                
                time.sleep(0.1)  # 避免请求过快
        
        self.all_data = all_records
        self.stats['total_records'] = len(all_records)
        
        print(f"\n[+] 处理完成:")
        print(f"  总文件数: {self.stats['total_files']}")
        print(f"  总记录数: {self.stats['total_records']}")
        print(f"  封面下载数: {self.stats['total_covers']}")
        print(f"  封面失败数: {self.stats['failed_covers']}")
    
    def save_results(self):
        """保存所有结果"""
        print(f"\n[*] 保存结果...")
        
        # 1. 保存整合后的数据 (JSON)
        data_file = os.path.join(self.output_dir, 'integrated_data.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_records': len(self.all_data),
                'records': self.all_data,
            }, f, ensure_ascii=False, indent=2)
        print(f"  [+] 数据文件: {data_file}")
        
        # 2. 保存整合后的数据 (CSV)
        csv_file = os.path.join(self.output_dir, 'integrated_data.csv')
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.STANDARD_FIELDS)
            writer.writeheader()
            for record in self.all_data:
                writer.writerow({k: record.get(k, '') for k in self.STANDARD_FIELDS})
        print(f"  [+] CSV文件: {csv_file}")
        
        # 3. 保存封面映射关系
        mapping_file = os.path.join(self.output_dir, 'cover_mapping.json')
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.cover_mapping, f, ensure_ascii=False, indent=2)
        print(f"  [+] 封面映射: {mapping_file}")
        
        # 4. 保存统计信息
        stats_file = os.path.join(self.output_dir, 'stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        print(f"  [+] 统计信息: {stats_file}")
        
        # 5. 生成前端数据库文件
        frontend_data = self.generate_frontend_data()
        frontend_file = os.path.join(self.output_dir, 'frontend_database.json')
        with open(frontend_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, ensure_ascii=False, indent=2)
        print(f"  [+] 前端数据: {frontend_file}")
        
        # 6. 复制到前端目录
        web_data_dir = os.path.join(os.path.dirname(self.output_dir), 'packages', 'web', 'public', 'data')
        os.makedirs(web_data_dir, exist_ok=True)
        
        import shutil
        shutil.copy(frontend_file, os.path.join(web_data_dir, 'video_database.json'))
        print(f"  [+] 已复制到前端目录")
    
    def generate_frontend_data(self) -> Dict:
        """生成前端展示数据"""
        # 按期数排序
        sorted_data = sorted(
            self.all_data,
            key=lambda x: (x.get('episode', 0), x.get('part', '')),
            reverse=True
        )
        
        return {
            'generated_at': datetime.now().isoformat(),
            'version': 'v1.0',
            'total_videos': len(sorted_data),
            'videos': sorted_data,
        }


def main():
    """主函数"""
    print("="*60)
    print("怖客 - CSV数据整合工具")
    print("="*60)
    
    download_dir = r"C:\Users\can\Downloads"
    output_dir = r"d:\怖客\scripts\csv_integrated"
    
    integrator = CSVDataIntegrator(download_dir, output_dir)
    
    # 处理所有文件
    integrator.process_all_files()
    
    # 保存结果
    integrator.save_results()
    
    print("\n" + "="*60)
    print("整合完成!")
    print("="*60)


if __name__ == "__main__":
    main()
