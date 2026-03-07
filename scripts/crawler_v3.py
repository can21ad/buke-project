#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - B站视频评论区智能爬虫 V3.0
==========================================
功能特性:
1. AI总结识别与提取
2. 往期故事智能提取与分类
3. "求出处"评论识别与回复追踪
4. BV号提取与优先爬取列表
5. 热度值计算机制
6. 结构化数据输出
"""

import requests
import re
import json
import time
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from datetime import datetime
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


# ==========================================
# 数据结构定义
# ==========================================

@dataclass
class Story:
    """故事数据结构"""
    name: str                          # 故事名称
    mention_count: int                 # 提及次数
    heat_score: float                  # 热度值
    bv_list: List[str]                 # 相关BV号列表
    time_markers: List[str]            # 时间标记列表
    comments: List[Dict]               # 相关评论
    category: str                      # 分类: 当期/往期/求助
    source_video: str                  # 来源视频标题
    source_bvid: str                   # 来源视频BV号


@dataclass  
class Comment:
    """评论数据结构"""
    rpid: str                          # 评论ID
    content: str                       # 评论内容
    like_count: int                    # 点赞数
    reply_count: int                   # 回复数
    author: str                        # 作者
    is_ai_summary: bool                # 是否为AI总结
    mentioned_stories: List[str]       # 提及的故事
    mentioned_bvs: List[str]           # 提及的BV号
    help_requests: List[str]           # 求助内容
    time_markers: List[str]            # 时间标记


@dataclass
class CrawlerResult:
    """爬虫结果数据结构"""
    generated_at: str                  # 生成时间
    source_video: str                  # 来源视频
    source_bvid: str                   # 来源BV号
    ai_summary: Optional[str]          # AI总结内容
    current_stories: List[Story]       # 当期故事
    past_stories: List[Story]          # 往期故事
    help_requests: List[Dict]          # 求助列表
    priority_bv_list: List[str]        # 优先爬取BV号列表
    total_comments: int                # 总评论数
    total_stories: int                 # 总故事数


# ==========================================
# 工具类
# ==========================================

class PatternMatcher:
    """模式匹配工具类"""
    
    # BV号模式
    BV_PATTERN = re.compile(r'BV[a-zA-Z0-9]{10}')
    
    # 时间标记模式 (支持多种格式)
    TIME_PATTERNS = [
        re.compile(r'(\d{1,2}:\d{2})'),                    # 12:34
        re.compile(r'(\d{1,2}:\d{2}:\d{2})'),              # 1:23:45
        re.compile(r'[(（](\d{1,2}:\d{2})[)）]'),          # (12:34) 或 （12:34）
        re.compile(r'第(\d+)期'),                          # 第123期
        re.compile(r'(\d+)分(\d+)秒'),                     # 12分34秒
    ]
    
    # AI总结识别模式
    AI_SUMMARY_PATTERNS = [
        re.compile(r'AI总结[：:](.*?)(?=AI总结[：:]|$)', re.DOTALL),
        re.compile(r'视频内容[：:](.*?)(?=视频内容[：:]|$)', re.DOTALL),
        re.compile(r'本期内容[：:](.*?)(?=本期内容[：:]|$)', re.DOTALL),
        re.compile(r'内容总结[：:](.*?)(?=内容总结[：:]|$)', re.DOTALL),
    ]
    
    # 求助模式
    HELP_PATTERNS = [
        re.compile(r'求.*?出处'),
        re.compile(r'求.*?推荐'),
        re.compile(r'找.*?故事'),
        re.compile(r'帮找.*?故事'),
        re.compile(r'求助.*?故事'),
        re.compile(r'那个.*?故事.*?在哪'),
        re.compile(r'第.*?个故事.*?是'),
        re.compile(r'几分几秒.*?故事'),
    ]
    
    # 故事名称模式 (道听途说XX期)
    STORY_NAME_PATTERNS = [
        re.compile(r'道听途说(\d+)[上下]?期?'),
        re.compile(r'第(\d+)期'),
        re.compile(r'(\d+)期'),
    ]
    
    # 故事关键词
    STORY_KEYWORDS = [
        '故事', '经历', '真实', '灵异', '恐怖', '诡异', '离奇',
        '鬼', '魂', '灵', '怪', '妖', '魔', '神', '仙',
        '老人', '小孩', '女人', '男人', '朋友', '亲戚',
        '房子', '房间', '楼', '村', '山', '水', '路',
    ]
    
    # 低质量评论模式
    LOW_QUALITY_PATTERNS = [
        re.compile(r'^[\d\s\.\,\!\?\!\?。！？，、]+$'),  # 纯数字/符号
        re.compile(r'^(哈哈|hhh|666|牛逼|卧槽|太强了|绝了|好家伙)+$'),  # 纯表情词
    ]
    
    @classmethod
    def extract_bv_numbers(cls, text: str) -> List[str]:
        """提取所有BV号"""
        return list(set(cls.BV_PATTERN.findall(text)))
    
    @classmethod
    def extract_time_markers(cls, text: str) -> List[str]:
        """提取所有时间标记"""
        markers = []
        for pattern in cls.TIME_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                for match in matches:
                    if isinstance(match, str):
                        markers.append(match)
                    elif isinstance(match, tuple):
                        markers.append(''.join(match))
        return list(set(markers))
    
    @classmethod
    def extract_ai_summary(cls, text: str) -> Optional[str]:
        """提取AI总结内容"""
        for pattern in cls.AI_SUMMARY_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None
    
    @classmethod
    def detect_help_requests(cls, text: str) -> List[str]:
        """检测求助内容"""
        requests = []
        for pattern in cls.HELP_PATTERNS:
            matches = pattern.findall(text)
            requests.extend(matches)
        return requests
    
    @classmethod
    def extract_story_names(cls, text: str) -> List[str]:
        """提取故事名称"""
        names = []
        for pattern in cls.STORY_NAME_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    match = ''.join(match)
                names.append(f"道听途说{match}期")
        return list(set(names))
    
    @classmethod
    def is_low_quality(cls, text: str) -> bool:
        """判断是否为低质量评论"""
        for pattern in cls.LOW_QUALITY_PATTERNS:
            if pattern.match(text.strip()):
                return True
        # 内容过短
        if len(text.strip()) < 15:
            return True
        return False
    
    @classmethod
    def has_story_content(cls, text: str) -> bool:
        """判断是否包含故事内容"""
        return any(kw in text for kw in cls.STORY_KEYWORDS)


# ==========================================
# 热度计算器
# ==========================================

class HeatScoreCalculator:
    """热度值计算器"""
    
    # 权重配置
    WEIGHTS = {
        'mention_count': 100,      # 提及次数权重
        'like_weight': 0.5,        # 点赞权重
        'reply_weight': 2,         # 回复权重
        'time_marker_weight': 50,  # 时间标记权重
        'bv_weight': 30,           # BV号权重
        'help_request_weight': 80, # 求助权重
        'recency_bonus': 20,       # 新近度加成
    }
    
    @classmethod
    def calculate(cls, story: Story, comment_stats: Dict) -> float:
        """
        计算故事热度值
        
        热度值 = 提及次数 * 100 + 
                 平均点赞 * 0.5 + 
                 平均回复 * 2 + 
                 时间标记数 * 50 + 
                 BV号数 * 30 + 
                 求助次数 * 80
        """
        score = 0.0
        
        # 提及次数得分
        score += story.mention_count * cls.WEIGHTS['mention_count']
        
        # 评论互动得分
        if story.comments:
            avg_likes = sum(c.get('like_count', 0) for c in story.comments) / len(story.comments)
            avg_replies = sum(c.get('reply_count', 0) for c in story.comments) / len(story.comments)
            score += avg_likes * cls.WEIGHTS['like_weight']
            score += avg_replies * cls.WEIGHTS['reply_weight']
        
        # 时间标记得分
        score += len(story.time_markers) * cls.WEIGHTS['time_marker_weight']
        
        # BV号得分
        score += len(story.bv_list) * cls.WEIGHTS['bv_weight']
        
        return round(score, 2)


# ==========================================
# 爬虫核心类
# ==========================================

class BilibiliCrawlerV3:
    """B站评论区爬虫 V3.0"""
    
    def __init__(self, cookie: str = ''):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://www.bilibili.com',
            'Cookie': cookie if cookie else 'buvid3=default; buvid4=default'
        }
        
        # 数据存储
        self.comments: List[Comment] = []
        self.stories: Dict[str, Story] = {}
        self.ai_summary: Optional[str] = None
        self.priority_bv_list: List[str] = []
        self.help_requests: List[Dict] = []
        
        # 统计数据
        self.total_comments = 0
        self.processed_bvids = set()
        
    def get_video_info(self, bvid: str) -> Optional[Dict]:
        """获取视频信息"""
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            data = response.json()
            if data['code'] == 0:
                return {
                    'aid': data['data']['aid'],
                    'title': data['data']['title'],
                    'bvid': bvid,
                    'desc': data['data'].get('desc', ''),
                    'duration': data['data'].get('duration', 0),
                    'pub_date': data['data'].get('pubdate', 0),
                    'view_count': data['data']['stat'].get('view', 0),
                    'comment_count': data['data']['stat'].get('reply', 0),
                }
        except Exception as e:
            print(f"[-] 获取视频信息失败: {e}")
        return None
    
    def fetch_comments(self, aid: int, pages: int = 10) -> List[Comment]:
        """
        按照时间顺序爬取评论
        
        Args:
            aid: 视频aid
            pages: 爬取页数 (默认10页)
        """
        print(f"[*] 开始爬取评论，目标: {pages}页")
        
        comments = []
        
        for page in range(1, pages + 1):
            # 使用mode=0按时间排序
            url = f"https://api.bilibili.com/x/v2/reply/main?type=1&oid={aid}&mode=0&pn={page}"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                data = response.json()
                
                if data['code'] != 0 or 'data' not in data:
                    print(f"[-] 第{page}页获取失败: {data.get('message', '未知错误')}")
                    break
                    
                if 'replies' not in data['data'] or not data['data']['replies']:
                    print(f"[*] 第{page}页无更多评论")
                    break
                
                replies = data['data']['replies']
                print(f"[+] 第{page}页获取到 {len(replies)} 条评论")
                
                for reply in replies:
                    content = reply['content']['message']
                    
                    # 跳过低质量评论
                    if PatternMatcher.is_low_quality(content):
                        continue
                    
                    comment = Comment(
                        rpid=str(reply['rpid']),
                        content=content,
                        like_count=reply.get('like', 0),
                        reply_count=reply.get('rcount', 0),
                        author=reply['member']['uname'],
                        is_ai_summary=False,
                        mentioned_stories=[],
                        mentioned_bvs=[],
                        help_requests=[],
                        time_markers=[]
                    )
                    
                    # 提取AI总结
                    ai_summary = PatternMatcher.extract_ai_summary(content)
                    if ai_summary:
                        comment.is_ai_summary = True
                        self.ai_summary = ai_summary
                        print(f"  [AI总结] 发现AI总结内容: {ai_summary[:50]}...")
                    
                    # 提取BV号
                    comment.mentioned_bvs = PatternMatcher.extract_bv_numbers(content)
                    if comment.mentioned_bvs:
                        self.priority_bv_list.extend(comment.mentioned_bvs)
                    
                    # 提取时间标记
                    comment.time_markers = PatternMatcher.extract_time_markers(content)
                    
                    # 提取故事名称
                    comment.mentioned_stories = PatternMatcher.extract_story_names(content)
                    
                    # 检测求助
                    comment.help_requests = PatternMatcher.detect_help_requests(content)
                    if comment.help_requests:
                        self.help_requests.append({
                            'comment_id': comment.rpid,
                            'author': comment.author,
                            'content': comment.content,
                            'requests': comment.help_requests,
                            'like_count': comment.like_count,
                        })
                    
                    comments.append(comment)
                
                time.sleep(0.3)  # 避免请求过快
                
            except Exception as e:
                print(f"[-] 第{page}页爬取异常: {e}")
                break
        
        self.total_comments = len(comments)
        print(f"[+] 评论爬取完成，共获取 {self.total_comments} 条有效评论")
        
        return comments
    
    def classify_and_extract_stories(self, comments: List[Comment], video_title: str, bvid: str):
        """
        对评论进行分类并提取故事信息
        """
        print("[*] 开始分类和提取故事信息...")
        
        # 提取当前视频期数
        current_episode = ""
        episode_match = re.search(r'道听途说(\d+)', video_title)
        if episode_match:
            current_episode = f"道听途说{episode_match.group(1)}期"
        
        # 故事统计字典
        story_stats: Dict[str, Dict] = defaultdict(lambda: {
            'mention_count': 0,
            'bv_list': set(),
            'time_markers': set(),
            'comments': [],
            'category': '往期',
        })
        
        for comment in comments:
            # 处理提及的往期故事
            for story_name in comment.mentioned_stories:
                if story_name != current_episode:
                    story_stats[story_name]['mention_count'] += 1
                    story_stats[story_name]['bv_list'].update(comment.mentioned_bvs)
                    story_stats[story_name]['time_markers'].update(comment.time_markers)
                    story_stats[story_name]['comments'].append({
                        'content': comment.content[:200],
                        'like_count': comment.like_count,
                        'reply_count': comment.reply_count,
                        'author': comment.author,
                    })
            
            # 处理包含时间标记的评论 (可能是当期故事)
            if comment.time_markers and not comment.mentioned_stories:
                # 使用时间标记作为故事标识
                for marker in comment.time_markers:
                    story_key = f"当期故事_{marker}"
                    story_stats[story_key]['mention_count'] += 1
                    story_stats[story_key]['time_markers'].add(marker)
                    story_stats[story_key]['category'] = '当期'
                    story_stats[story_key]['comments'].append({
                        'content': comment.content[:200],
                        'like_count': comment.like_count,
                        'reply_count': comment.reply_count,
                        'author': comment.author,
                    })
            
            # 处理包含故事关键词但没有明确期数的评论
            if PatternMatcher.has_story_content(comment.content) and not comment.mentioned_stories:
                # 提取可能的故事名称 (使用评论中的关键词组合)
                if comment.time_markers:
                    story_key = f"故事_{comment.time_markers[0]}"
                    story_stats[story_key]['mention_count'] += 1
                    story_stats[story_key]['time_markers'].update(comment.time_markers)
                    story_stats[story_key]['bv_list'].update(comment.mentioned_bvs)
                    story_stats[story_key]['comments'].append({
                        'content': comment.content[:200],
                        'like_count': comment.like_count,
                        'reply_count': comment.reply_count,
                        'author': comment.author,
                    })
        
        # 转换为Story对象并计算热度
        for name, stats in story_stats.items():
            story = Story(
                name=name,
                mention_count=stats['mention_count'],
                heat_score=0,  # 稍后计算
                bv_list=list(stats['bv_list']),
                time_markers=list(stats['time_markers']),
                comments=stats['comments'][:10],  # 只保留前10条相关评论
                category=stats['category'],
                source_video=video_title,
                source_bvid=bvid,
            )
            story.heat_score = HeatScoreCalculator.calculate(story, {})
            self.stories[name] = story
        
        print(f"[+] 故事提取完成，共发现 {len(self.stories)} 个故事")
    
    def run(self, bvid: str, pages: int = 10) -> CrawlerResult:
        """
        执行爬虫主流程
        
        Args:
            bvid: 视频BV号
            pages: 爬取评论页数
        """
        print("=" * 60)
        print("怖客智能爬虫 V3.0 启动...")
        print(f"目标视频: {bvid}")
        print(f"爬取页数: {pages}页")
        print("=" * 60)
        
        # 1. 获取视频信息
        video_info = self.get_video_info(bvid)
        if not video_info:
            print("[-] 无法获取视频信息，退出...")
            return None
        
        print(f"[+] 视频标题: {video_info['title']}")
        print(f"[+] 视频时长: {video_info['duration']//60}分钟")
        print(f"[+] 评论数量: {video_info['comment_count']}")
        
        # 2. 爬取评论
        self.comments = self.fetch_comments(video_info['aid'], pages)
        
        if not self.comments:
            print("[-] 未获取到评论，退出...")
            return None
        
        # 3. 分类和提取故事
        self.classify_and_extract_stories(
            self.comments, 
            video_info['title'], 
            bvid
        )
        
        # 4. 去重BV号列表
        self.priority_bv_list = list(set(self.priority_bv_list))
        
        # 5. 分类故事
        current_stories = [s for s in self.stories.values() if s.category == '当期']
        past_stories = [s for s in self.stories.values() if s.category == '往期']
        
        # 按热度排序
        current_stories.sort(key=lambda x: x.heat_score, reverse=True)
        past_stories.sort(key=lambda x: x.heat_score, reverse=True)
        
        # 6. 生成结果
        result = CrawlerResult(
            generated_at=datetime.now().isoformat(),
            source_video=video_info['title'],
            source_bvid=bvid,
            ai_summary=self.ai_summary,
            current_stories=[asdict(s) for s in current_stories],
            past_stories=[asdict(s) for s in past_stories],
            help_requests=self.help_requests[:20],  # 只保留前20条求助
            priority_bv_list=self.priority_bv_list,
            total_comments=self.total_comments,
            total_stories=len(self.stories),
        )
        
        print(f"\n{'='*60}")
        print(f"[+] 爬虫执行完毕!")
        print(f"[+] 总评论数: {self.total_comments}")
        print(f"[+] 当期故事: {len(current_stories)}个")
        print(f"[+] 往期故事: {len(past_stories)}个")
        print(f"[+] 求助请求: {len(self.help_requests)}条")
        print(f"[+] 待爬取BV号: {len(self.priority_bv_list)}个")
        if self.ai_summary:
            print(f"[+] AI总结: 已提取")
        print(f"{'='*60}")
        
        return result


# ==========================================
# 主程序
# ==========================================

def save_result(result: CrawlerResult, output_file: str = 'buke_crawler_v3.json'):
    """保存结果到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(asdict(result), f, ensure_ascii=False, indent=2)
    print(f"[+] 结果已保存至: {output_file}")


def main():
    """主函数"""
    # Cookie配置 (必须填写有效的B站Cookie)
    cookie = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; __itrace_wid=fd682858-9fa6-4ccb-28b2-a82e62ee6170; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3MDM3MDUsImlhdCI6MTc3MjQ0NDQ0NSwicGx0IjotMX0.jJ8uRdHhcV20bl1uTXzBZcP-obdgB7EFRArutjbbkXc; bili_ticket_expires=1772703645; SESSDATA=2472a2ba%2C1788001684%2C9597f%2A32CjCu75QuNog6ez4sRyS7UWd6z7Dz2bgwMqaehPf-a6TFPpB459i5lam46JdKNH0r0Z8SVjNEcTNPem5pV2k4ODg3cV9oU0RwWXFHdUlpbC0ydUZLRXdyRFJwMDZCMW5nNDZBRG5LZTJ1QzFLcXAyV29KTTNaelUxMHFkLU1KVFFramZkalFxMnpBIIEC; bili_jct=019f8b4045241197796aace28d79a311; sid=575k0iix; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bp_t_offset_16107971=1175944487818493952; CURRENT_FNVAL=4048; b_lsid=6DF899DC_19CB99459D0"
    
    # 初始化爬虫
    crawler = BilibiliCrawlerV3(cookie=cookie)
    
    # 目标BV号列表 (大佬何金银最新视频)
    target_bvids = [
        "BV1Gg6iB9EbS",  # 【道听途说特辑】三小时
        "BV1D1qpB6ECc",  # 【道听途说165上】乐山外卖员
        "BV19SiFB1E1q",  # 【道听途说166下】恐怖老人
    ]
    
    # 爬取多个视频
    all_results = []
    for bvid in target_bvids:
        # 提升每个视频爬取页数到 50 页
        result = crawler.run(bvid, pages=50)
        if result:
            all_results.append(asdict(result))
            save_result(result, f'buke_v3_{bvid}.json')
        
        # 重置爬虫状态
        crawler = BilibiliCrawlerV3(cookie=cookie)
        # 评论页数增多后适当拉长间隔，减轻风控压力
        time.sleep(3)
    
    # 合并结果
    if all_results:
        merged_result = {
            'generated_at': datetime.now().isoformat(),
            'total_videos': len(all_results),
            'results': all_results,
        }
        
        with open('buke_crawler_v3_merged.json', 'w', encoding='utf-8') as f:
            json.dump(merged_result, f, ensure_ascii=False, indent=2)
        print(f"\n[+] 合并结果已保存至: buke_crawler_v3_merged.json")


if __name__ == "__main__":
    main()