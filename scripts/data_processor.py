#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - 数据处理脚本
==========================================
对采集的评论数据进行清洗、标准化和关键词提取
"""

import os
import sys
import json
import re
import jieba
import jieba.analyse
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class DataProcessor:
    """数据处理与关键词提取"""
    
    # 停用词列表
    STOPWORDS = set([
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '什么', '他', '她', '它', '们', '这个', '那个', '这些', '那些',
        '可以', '没', '啊', '呢', '吧', '嘛', '哦', '哈', '嘿', '嗯', '呀', '哎', '唉',
        '真的', '还是', '但是', '因为', '所以', '如果', '虽然', '而且', '或者', '然后',
        '就是', '可能', '应该', '已经', '这样', '那样', '怎样', '这么', '那么', '多么',
        '一下', '一些', '一点', '一直', '一起', '一定', '一样', '一般', '一边', '一方面',
        'up', 'UP', '主', '视频', '评论', '故事', '道听途说', '大佬', '何金银',
        '哈哈哈', '哈哈哈哈', '哈哈哈哈哈', '笑', '笑死', '太', '真', '更', '多',
        '觉得', '感觉', '知道', '看到', '听到', '想到', '发现', '觉得', '认为',
        '希望', '期待', '支持', '加油', '感谢', '谢谢', '感谢', '点赞', '投币',
        '收藏', '转发', '分享', '关注', '订阅', '三连', '一键三连',
    ])
    
    # 故事相关关键词（增加权重）
    STORY_KEYWORDS = set([
        '灵异', '恐怖', '鬼', '鬼故事', '真实', '经历', '事件', '怪事', '诡异',
        '惊悚', '吓人', '害怕', '毛骨悚然', '不可思议', '神秘', '超自然',
        '鬼魂', '幽灵', '妖怪', '怪物', '恶魔', '邪灵', '附身', '诅咒',
        '阴阳', '风水', '算命', '占卜', '预言', '梦境', '预知',
        '医院', '学校', '老房子', '墓地', '荒村', '深山', '森林',
        '夜晚', '凌晨', '午夜', '深夜', '傍晚', '黎明',
    ])
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.input_dir = os.path.join(self.base_dir, 'diverse_data')
        self.output_dir = os.path.join(self.base_dir, 'processed_data')
        
        self._setup_directories()
        self._setup_jieba()
        
        self.raw_data = []
        self.processed_data = []
        self.keyword_url_map = defaultdict(list)
    
    def _setup_directories(self):
        """创建输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _setup_jieba(self):
        """配置jieba分词"""
        # 添加故事相关词汇到词典
        for word in self.STORY_KEYWORDS:
            jieba.add_word(word, freq=1000)
        
        # 添加常见故事主题词
        story_themes = [
            '三霄娘娘', '黄皮子', '狐仙', '蛇精', '水鬼', '吊死鬼',
            '笔仙', '碟仙', '通灵', '招魂', '驱鬼', '捉鬼',
            '阴阳眼', '天眼', '鬼打墙', '鬼压床', '鬼上身',
            '轮回', '前世', '来世', '因果', '报应',
        ]
        for word in story_themes:
            jieba.add_word(word, freq=800)
    
    def load_data(self) -> List[Dict]:
        """加载采集的数据"""
        print("[*] 加载采集数据...")
        
        # 尝试加载合并文件
        merged_file = os.path.join(self.input_dir, 'diverse_collection_merged.json')
        if os.path.exists(merged_file):
            with open(merged_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.raw_data = data.get('videos', [])
                print(f"[+] 从合并文件加载 {len(self.raw_data)} 个视频数据")
                return self.raw_data
        
        # 否则加载单独的文件
        video_files = [f for f in os.listdir(self.input_dir) if f.startswith('video_') and f.endswith('.json')]
        
        for vf in video_files:
            with open(os.path.join(self.input_dir, vf), 'r', encoding='utf-8') as f:
                self.raw_data.append(json.load(f))
        
        print(f"[+] 加载 {len(self.raw_data)} 个视频数据")
        return self.raw_data
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""
        
        # 移除表情符号
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？、；：""''（）【】《》]', '', text)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def standardize_comment(self, comment: Dict, video_info: Dict) -> Dict:
        """标准化单条评论"""
        return {
            'content': self.clean_text(comment.get('content', '')),
            'like_count': comment.get('like_count', 0),
            'video_bvid': video_info.get('source_bvid', ''),
            'video_title': video_info.get('source_video', ''),
            'video_url': f"https://www.bilibili.com/video/{video_info.get('source_bvid', '')}",
            'time_markers': comment.get('time_markers', []),
            'is_help_request': comment.get('is_help_request', False),
            'is_ai_summary': comment.get('is_ai_summary', False),
        }
    
    def process_video_data(self, video_data: Dict) -> Dict:
        """处理单个视频数据"""
        processed = {
            'source_bvid': video_data.get('source_bvid', ''),
            'source_video': video_data.get('source_video', ''),
            'video_url': f"https://www.bilibili.com/video/{video_data.get('source_bvid', '')}",
            'total_comments': video_data.get('total_comments', 0),
            'comments': [],
            'past_stories': [],
        }
        
        # 处理评论
        raw_comments = video_data.get('comments', [])
        for comment in raw_comments:
            std_comment = self.standardize_comment(comment, video_data)
            if std_comment['content']:  # 只保留有内容的评论
                processed['comments'].append(std_comment)
        
        # 处理故事
        past_stories = video_data.get('past_stories', [])
        for story in past_stories:
            story_data = {
                'name': story.get('name', ''),
                'heat_score': story.get('heat_score', 0),
                'mention_count': story.get('mention_count', 0),
                'video_url': processed['video_url'],
                'video_bvid': processed['source_bvid'],
                'comments': [self.clean_text(c.get('content', '')) for c in story.get('comments', [])],
            }
            processed['past_stories'].append(story_data)
        
        return processed
    
    def process_all_data(self) -> List[Dict]:
        """处理所有数据"""
        print("\n[*] 开始处理数据...")
        
        self.processed_data = []
        for video in self.raw_data:
            processed = self.process_video_data(video)
            self.processed_data.append(processed)
        
        print(f"[+] 处理完成: {len(self.processed_data)} 个视频")
        return self.processed_data
    
    def extract_keywords_tfidf(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """使用TF-IDF提取关键词"""
        keywords = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=True,
            allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vd', 'vn', 'a', 'ad', 'an')
        )
        return [(word, weight) for word, weight in keywords if word not in self.STOPWORDS]
    
    def extract_keywords_textrank(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """使用TextRank提取关键词"""
        keywords = jieba.analyse.textrank(
            text,
            topK=top_k,
            withWeight=True,
            allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vd', 'vn', 'a', 'ad', 'an')
        )
        return [(word, weight) for word, weight in keywords if word not in self.STOPWORDS]
    
    def extract_keywords_hybrid(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """混合方法提取关键词（TF-IDF + TextRank）"""
        tfidf_keywords = dict(self.extract_keywords_tfidf(text, top_k * 2))
        textrank_keywords = dict(self.extract_keywords_textrank(text, top_k * 2))
        
        # 合并权重
        combined = defaultdict(float)
        for word, weight in tfidf_keywords.items():
            combined[word] += weight * 0.5
        for word, weight in textrank_keywords.items():
            combined[word] += weight * 0.5
        
        # 故事关键词加权
        for word in combined:
            if word in self.STORY_KEYWORDS:
                combined[word] *= 1.5
        
        # 排序并返回
        sorted_keywords = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords[:top_k]
    
    def build_keyword_url_map(self) -> Dict:
        """构建关键词-网址对应关系表"""
        print("\n[*] 构建关键词-网址对应关系表...")
        
        self.keyword_url_map = defaultdict(list)
        
        for video in self.processed_data:
            video_url = video['video_url']
            video_bvid = video['source_bvid']
            video_title = video['source_video']
            
            # 从视频标题提取关键词
            title_keywords = self.extract_keywords_hybrid(video_title, 5)
            for keyword, weight in title_keywords:
                self.keyword_url_map[keyword].append({
                    'url': video_url,
                    'bvid': video_bvid,
                    'title': video_title,
                    'weight': weight,
                    'source': 'title'
                })
            
            # 从评论提取关键词
            all_comments = ' '.join([c['content'] for c in video['comments'][:100]])
            if all_comments:
                comment_keywords = self.extract_keywords_hybrid(all_comments, 15)
                for keyword, weight in comment_keywords:
                    # 避免重复添加同一视频
                    existing = [x for x in self.keyword_url_map[keyword] if x['bvid'] == video_bvid]
                    if not existing:
                        self.keyword_url_map[keyword].append({
                            'url': video_url,
                            'bvid': video_bvid,
                            'title': video_title,
                            'weight': weight,
                            'source': 'comment'
                        })
            
            # 从故事名称提取关键词
            for story in video['past_stories']:
                story_keywords = self.extract_keywords_hybrid(story['name'], 5)
                for keyword, weight in story_keywords:
                    existing = [x for x in self.keyword_url_map[keyword] if x['bvid'] == video_bvid]
                    if not existing:
                        self.keyword_url_map[keyword].append({
                            'url': video_url,
                            'bvid': video_bvid,
                            'title': video_title,
                            'weight': weight * 1.2,  # 故事关键词加权
                            'source': 'story'
                        })
        
        # 对每个关键词的URL列表按权重排序
        for keyword in self.keyword_url_map:
            self.keyword_url_map[keyword] = sorted(
                self.keyword_url_map[keyword],
                key=lambda x: x['weight'],
                reverse=True
            )
        
        print(f"[+] 提取了 {len(self.keyword_url_map)} 个关键词")
        return dict(self.keyword_url_map)
    
    def check_diversity(self) -> Dict:
        """检查数据多样性"""
        print("\n[*] 检查数据多样性...")
        
        bvid_counts = Counter()
        url_counts = Counter()
        
        for keyword, urls in self.keyword_url_map.items():
            for item in urls:
                bvid_counts[item['bvid']] += 1
                url_counts[item['url']] += 1
        
        total_keywords = len(self.keyword_url_map)
        unique_bvids = len(bvid_counts)
        unique_urls = len(url_counts)
        
        # 计算集中度
        if total_keywords > 0:
            top_bvid = bvid_counts.most_common(1)[0] if bvid_counts else ('', 0)
            concentration = top_bvid[1] / sum(bvid_counts.values()) if bvid_counts else 0
        else:
            concentration = 1
        
        diversity_report = {
            'total_keywords': total_keywords,
            'unique_videos': unique_bvids,
            'unique_urls': unique_urls,
            'concentration_ratio': round(concentration, 3),
            'is_diverse': concentration < 0.3 and unique_bvids >= 10,
            'bvid_distribution': dict(bvid_counts.most_common(20)),
        }
        
        print(f"  关键词总数: {total_keywords}")
        print(f"  唯一视频数: {unique_bvids}")
        print(f"  集中度: {concentration:.2%}")
        print(f"  多样性: {'合格' if diversity_report['is_diverse'] else '不合格'}")
        
        return diversity_report
    
    def generate_frontend_data(self) -> Dict:
        """生成前端展示数据"""
        print("\n[*] 生成前端展示数据...")
        
        # 按关键词权重排序
        sorted_keywords = sorted(
            self.keyword_url_map.items(),
            key=lambda x: sum(item['weight'] for item in x[1]),
            reverse=True
        )
        
        # 生成故事列表（每个关键词对应一个故事条目）
        stories = []
        story_id = 0
        
        for keyword, urls in sorted_keywords[:100]:  # 取前100个关键词
            story_id += 1
            
            # 选择权重最高的URL
            best_match = urls[0] if urls else {}
            
            # 合并同关键词的所有视频标题
            related_titles = list(set(item['title'][:50] for item in urls[:3]))
            
            story = {
                'id': story_id,
                'name': keyword,
                'title': best_match.get('title', '')[:50],
                'bvid': best_match.get('bvid', ''),
                'video_url': best_match.get('url', ''),
                'heat': int(sum(item['weight'] for item in urls) * 100),
                'mention_count': len(urls),
                'related_videos': [
                    {'bvid': item['bvid'], 'title': item['title'][:30], 'url': item['url']}
                    for item in urls[:5]
                ],
                'tags': [keyword] + [k for k, _ in sorted_keywords[story_id:story_id+3] if k != keyword][:3],
            }
            stories.append(story)
        
        frontend_data = {
            'generated_at': datetime.now().isoformat(),
            'version': 'diverse_v1.0',
            'total_stories': len(stories),
            'theme': '【道听途说系列】热门关键词精选',
            'keywords': [k for k, _ in sorted_keywords[:20]],
            'stories': stories,
        }
        
        return frontend_data
    
    def save_all_outputs(self):
        """保存所有输出文件"""
        print("\n[*] 保存输出文件...")
        
        # 1. 保存处理后的数据
        processed_file = os.path.join(self.output_dir, 'processed_data.json')
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_videos': len(self.processed_data),
                'videos': self.processed_data,
            }, f, ensure_ascii=False, indent=2)
        print(f"  [+] 处理后数据: {processed_file}")
        
        # 2. 保存关键词-URL对应表
        keyword_map_file = os.path.join(self.output_dir, 'keyword_url_map.json')
        with open(keyword_map_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.keyword_url_map), f, ensure_ascii=False, indent=2)
        print(f"  [+] 关键词-URL对应表: {keyword_map_file}")
        
        # 3. 保存多样性报告
        diversity_report = self.check_diversity()
        diversity_file = os.path.join(self.output_dir, 'diversity_report.json')
        with open(diversity_file, 'w', encoding='utf-8') as f:
            json.dump(diversity_report, f, ensure_ascii=False, indent=2)
        print(f"  [+] 多样性报告: {diversity_file}")
        
        # 4. 保存前端数据
        frontend_data = self.generate_frontend_data()
        frontend_file = os.path.join(self.output_dir, 'frontend_data.json')
        with open(frontend_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, ensure_ascii=False, indent=2)
        print(f"  [+] 前端数据: {frontend_file}")
        
        # 5. 复制到前端目录
        web_data_dir = os.path.join(self.base_dir, '..', 'packages', 'web', 'public', 'data')
        os.makedirs(web_data_dir, exist_ok=True)
        
        import shutil
        shutil.copy(frontend_file, os.path.join(web_data_dir, 'buke_top_stories.json'))
        print(f"  [+] 已复制到前端目录")
        
        return {
            'processed_file': processed_file,
            'keyword_map_file': keyword_map_file,
            'diversity_file': diversity_file,
            'frontend_file': frontend_file,
        }
    
    def run_full_pipeline(self) -> Dict:
        """执行完整处理流程"""
        print("="*60)
        print("怖客 - 数据处理流程")
        print("="*60)
        
        # 1. 加载数据
        self.load_data()
        
        if not self.raw_data:
            print("[-] 没有可处理的数据")
            return {'success': False, 'error': 'No data to process'}
        
        # 2. 处理数据
        self.process_all_data()
        
        # 3. 构建关键词-URL对应表
        self.build_keyword_url_map()
        
        # 4. 检查多样性
        diversity = self.check_diversity()
        
        # 5. 保存输出
        outputs = self.save_all_outputs()
        
        print("\n" + "="*60)
        print("处理完成摘要")
        print("="*60)
        print(f"处理视频数: {len(self.processed_data)}")
        print(f"提取关键词: {len(self.keyword_url_map)}")
        print(f"数据多样性: {'合格' if diversity['is_diverse'] else '不合格'}")
        
        return {
            'success': True,
            'diversity': diversity,
            'outputs': outputs,
        }


def main():
    """主函数"""
    processor = DataProcessor()
    result = processor.run_full_pipeline()
    
    if result['success']:
        print("\n[+] 数据处理完成!")
    else:
        print(f"\n[-] 处理失败: {result.get('error')}")


if __name__ == "__main__":
    main()
