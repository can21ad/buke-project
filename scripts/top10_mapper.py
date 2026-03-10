#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOP10视频与CSV数据库映射工具
建立BV号对应关系，优先处理TOP10视频
"""

import json
import csv
import os
from typing import List, Dict, Optional, Tuple

class Top10Mapper:
    """TOP10映射器"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.top10_data = None
        self.csv_data = {}
        self.mapping = []
    
    def load_top10_data(self) -> List[Dict]:
        """加载TOP10视频数据"""
        top10_path = os.path.join(
            self.project_root, 
            'packages', 'web', 'public', 'data', 'top10_help_comments.json'
        )
        
        with open(top10_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.top10_data = data['videos']
        
        print(f"[OK] 加载TOP10数据: {len(self.top10_data)} 个视频")
        return self.top10_data
    
    def load_csv_data(self) -> Dict[str, Dict]:
        """加载CSV数据库"""
        csv_path = os.path.join(self.project_root, 'scripts', 'space_merged.csv')
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bvid = row.get('bvid', '')
                if bvid:
                    self.csv_data[bvid] = row
        
        print(f"[OK] 加载CSV数据: {len(self.csv_data)} 个视频")
        return self.csv_data
    
    def create_mapping(self) -> List[Dict]:
        """创建TOP10与CSV的映射关系"""
        if not self.top10_data:
            self.load_top10_data()
        if not self.csv_data:
            self.load_csv_data()
        
        print("\n[*] 建立映射关系...")
        print("="*80)
        
        for video in self.top10_data:
            bvid = video['bvid']
            rank = video['rank']
            title = video['title']
            episode = video.get('episode', 0)
            
            # 在CSV中查找对应
            csv_record = self.csv_data.get(bvid)
            
            mapping_item = {
                'rank': rank,
                'bvid': bvid,
                'title': title,
                'episode': episode,
                'play_count': video.get('play_count', 0),
                'comment_count': video.get('comment_count', 0),
                'in_csv': csv_record is not None,
                'csv_title': csv_record.get('title', '') if csv_record else None,
                'csv_views': csv_record.get('views', '') if csv_record else None,
            }
            
            self.mapping.append(mapping_item)
            
            # 打印映射信息
            status = "✓ 已匹配" if csv_record else "✗ 未找到"
            print(f"Rank {rank:2d} | {bvid} | {status}")
            print(f"       TOP10标题: {title[:50]}...")
            if csv_record:
                print(f"       CSV标题:   {csv_record.get('title', '')[:50]}...")
            print()
        
        return self.mapping
    
    def get_top10_bvids(self) -> List[str]:
        """获取TOP10的BV号列表"""
        if not self.mapping:
            self.create_mapping()
        return [item['bvid'] for item in self.mapping]
    
    def get_mapped_summary(self) -> str:
        """获取映射摘要"""
        if not self.mapping:
            self.create_mapping()
        
        total = len(self.mapping)
        matched = sum(1 for item in self.mapping if item['in_csv'])
        
        summary = f"""
映射关系摘要
{'='*80}
总视频数: {total}
成功匹配: {matched}
未匹配:   {total - matched}

TOP10视频列表:
"""
        for item in self.mapping:
            status = "✓" if item['in_csv'] else "✗"
            summary += f"{status} Rank {item['rank']:2d} | {item['bvid']} | 第{item['episode']:3d}期\n"
        
        return summary
    
    def export_bvid_list(self, output_file: str = 'top10_bvids.txt'):
        """导出BV号列表"""
        bvids = self.get_top10_bvids()
        output_path = os.path.join(self.project_root, 'scripts', output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for bvid in bvids:
                f.write(f"{bvid}\n")
        
        print(f"[OK] BV号列表已导出: {output_path}")
        return output_path
    
    def print_detailed_mapping(self):
        """打印详细映射信息"""
        if not self.mapping:
            self.create_mapping()
        
        print("\n" + "="*80)
        print("详细映射关系")
        print("="*80)
        
        for item in self.mapping:
            print(f"\nRank {item['rank']} - {item['bvid']}")
            print(f"  期数: 第{item['episode']}期")
            print(f"  播放量: {item['play_count']:,}")
            print(f"  求助评论: {item['comment_count']}条")
            print(f"  CSV匹配: {'是' if item['in_csv'] else '否'}")
            print(f"  标题: {item['title'][:60]}...")


def main():
    """主函数"""
    print("TOP10视频映射工具")
    print("="*80)
    
    mapper = Top10Mapper()
    
    # 创建映射
    mapper.create_mapping()
    
    # 打印摘要
    print(mapper.get_mapped_summary())
    
    # 打印详细信息
    mapper.print_detailed_mapping()
    
    # 导出BV号列表
    output_file = mapper.export_bvid_list()
    
    print(f"\n[OK] 完成！BV号列表已保存到: {output_file}")
    print("可以使用 ai_video_summarizer_pro.py 批量处理这些视频")


if __name__ == "__main__":
    main()