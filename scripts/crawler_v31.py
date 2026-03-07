#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - B站视频评论区智能爬虫 V3.1
==========================================
更新内容:
1. 大幅提高求助往期故事评论权重
2. 增强AI总结识别能力
3. 爬取页数增加到25页
4. 规范评论格式识别
"""

import requests
import re
import json
import time
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime


# ==========================================
# 配置常量
# ==========================================

# 爬取页数
MAX_PAGES = 25

# 权重配置
WEIGHTS = {
    # 基础权重
    'mention_count': 100,      # 提及次数权重
    'like_weight': 0.5,        # 点赞权重
    'reply_weight': 2,         # 回复权重
    'time_marker_weight': 50,  # 时间标记权重
    'bv_weight': 30,           # BV号权重
    
    # 高权重项目 (新增)
    'help_request_weight': 500,    # 求助往期故事权重 (大幅提高)
    'ai_summary_weight': 400,      # AI总结权重 (大幅提高)
    'story_name_weight': 200,      # 明确故事名称权重
    'time_with_story_weight': 300, # 时间+故事组合权重
    
    # 规范评论格式权重
    'standard_format_weight': 350,  # 规范格式评论权重
}


# ==========================================
# 模式匹配器
# ==========================================

class PatternMatcher:
    """模式匹配工具类"""
    
    # BV号模式
    BV_PATTERN = re.compile(r'BV[a-zA-Z0-9]{10}')
    
    # 时间标记模式
    TIME_PATTERNS = [
        re.compile(r'(\d{1,2}:\d{2})'),
        re.compile(r'(\d{1,2}:\d{2}:\d{2})'),
        re.compile(r'[(（](\d{1,2}:\d{2})[)）]'),
        re.compile(r'(\d+)分(\d+)秒'),
    ]
    
    # AI总结模式 (增强版)
    AI_SUMMARY_PATTERNS = [
        re.compile(r'AI总结[：:]\s*(.*?)(?=AI总结[：:]|$)', re.DOTALL),
        re.compile(r'视频内容[：:]\s*(.*?)(?=视频内容[：:]|$)', re.DOTALL),
        re.compile(r'本期内容[：:]\s*(.*?)(?=本期内容[：:]|$)', re.DOTALL),
        re.compile(r'内容总结[：:]\s*(.*?)(?=内容总结[：:]|$)', re.DOTALL),
        re.compile(r'故事总结[：:]\s*(.*?)(?=故事总结[：:]|$)', re.DOTALL),
        re.compile(r'本集内容[：:]\s*(.*?)(?=本集内容[：:]|$)', re.DOTALL),
    ]
    
    # 求助往期故事模式 (增强版 - 规范格式)
    HELP_REQUEST_PATTERNS = [
        # 规范格式: "求第X期的XX故事"
        re.compile(r'求第(\d+)期.*?故事'),
        re.compile(r'求.*?第(\d+)期'),
        re.compile(r'找第(\d+)期.*?故事'),
        # 规范格式: "X分X秒的故事叫什么"
        re.compile(r'(\d{1,2}:\d{2}).*?故事.*?[?？]'),
        re.compile(r'(\d{1,2}:\d{2}).*?叫什么'),
        re.compile(r'(\d{1,2}:\d{2}).*?是哪个'),
        # 规范格式: "那个XX的故事"
        re.compile(r'那个.*?故事.*?[?？]'),
        re.compile(r'那个.*?在哪'),
        re.compile(r'那个.*?叫什么'),
        # 规范格式: "求助找XX故事"
        re.compile(r'求助.*?找.*?故事'),
        re.compile(r'帮忙找.*?故事'),
        re.compile(r'求出处.*?故事'),
        # 规范格式: "第X个故事是哪个"
        re.compile(r'第(\d+)个故事.*?[?？]'),
        re.compile(r'第(\d+)个.*?是哪个'),
        # 规范格式: "X分X秒是什么故事"
        re.compile(r'(\d{1,2}:\d{2}).*?是什么'),
        re.compile(r'(\d{1,2}:\d{2}).*?讲的是'),
    ]
    
    # 故事名称模式
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
        '梦', '睡', '醒', '死', '活', '走', '来', '去',
    ]
    
    # 低质量评论模式
    LOW_QUALITY_PATTERNS = [
        re.compile(r'^[\d\s\.\,\!\?\!\?。！？，、]+$'),
        re.compile(r'^(哈哈|hhh|666|牛逼|卧槽|太强了|绝了|好家伙|笑死|笑喷)+$'),
        re.compile(r'^\[.*?\]+$'),  # 纯表情
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
                content = match.group(1).strip()
                if len(content) > 20:  # 确保有实质内容
                    return content
        return None
    
    @classmethod
    def detect_help_requests(cls, text: str) -> List[Dict]:
        """检测求助内容 (增强版)"""
        requests = []
        for pattern in cls.HELP_REQUEST_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    match = ''.join(match)
                requests.append({
                    'pattern': pattern.pattern[:30],
                    'matched': match,
                    'content': text[:100]
                })
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
        if len(text.strip()) < 15:
            return True
        return False
    
    @classmethod
    def has_story_content(cls, text: str) -> bool:
        """判断是否包含故事内容"""
        return any(kw in text for kw in cls.STORY_KEYWORDS)
    
    @classmethod
    def is_standard_help_format(cls, text: str) -> bool:
        """判断是否为规范求助格式"""
        # 规范格式特征:
        # 1. 包含时间点 + "故事" 关键词
        # 2. 包含 "求" + 期数
        # 3. 包含 "那个" + 故事相关词
        
        has_time = bool(cls.extract_time_markers(text))
        has_story = '故事' in text
        has_request = any(w in text for w in ['求', '找', '求助', '帮忙'])
        has_question = '?' in text or '？' in text or '什么' in text or '哪个' in text
        
        # 规范格式: 时间点 + 故事 + 疑问
        if has_time and has_story and has_question:
            return True
        # 规范格式: 求/找 + 期数/故事
        if has_request and (has_story or '期' in text):
            return True
        
        return False


# ==========================================
# 热度计算器
# ==========================================

class HeatScoreCalculator:
    """热度值计算器 V3.1"""
    
    @classmethod
    def calculate(cls, story_data: Dict) -> float:
        """
        计算故事热度值 (增强版)
        
        热度值 = 基础热度 + 求助热度 + AI总结热度 + 规范格式热度
        """
        score = 0.0
        
        # 1. 基础热度
        score += story_data.get('mention_count', 0) * WEIGHTS['mention_count']
        
        # 2. 评论互动热度
        comments = story_data.get('comments', [])
        if comments:
            avg_likes = sum(c.get('like_count', 0) for c in comments) / len(comments)
            avg_replies = sum(c.get('reply_count', 0) for c in comments) / len(comments)
            score += avg_likes * WEIGHTS['like_weight']
            score += avg_replies * WEIGHTS['reply_weight']
        
        # 3. 时间标记热度
        time_markers = story_data.get('time_markers', [])
        score += len(time_markers) * WEIGHTS['time_marker_weight']
        
        # 4. BV号热度
        bv_list = story_data.get('bv_list', [])
        score += len(bv_list) * WEIGHTS['bv_weight']
        
        # 5. 求助热度 (高权重)
        help_count = story_data.get('help_request_count', 0)
        score += help_count * WEIGHTS['help_request_weight']
        
        # 6. 规范格式热度 (高权重)
        standard_count = story_data.get('standard_format_count', 0)
        score += standard_count * WEIGHTS['standard_format_weight']
        
        # 7. 时间+故事组合热度 (高权重)
        time_story_count = story_data.get('time_with_story_count', 0)
        score += time_story_count * WEIGHTS['time_with_story_weight']
        
        return round(score, 2)


# ==========================================
# 爬虫核心类
# ==========================================

class BilibiliCrawlerV31:
    """B站评论区爬虫 V3.1"""
    
    def __init__(self, cookie: str = ''):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://www.bilibili.com',
            'Cookie': cookie if cookie else 'buvid3=default; buvid4=default'
        }
        
        # 数据存储
        self.ai_summaries: List[str] = []
        self.help_requests: List[Dict] = []
        self.story_stats: Dict[str, Dict] = defaultdict(lambda: {
            'mention_count': 0,
            'bv_list': set(),
            'time_markers': set(),
            'comments': [],
            'help_request_count': 0,
            'standard_format_count': 0,
            'time_with_story_count': 0,
            'category': '往期',
        })
        self.priority_bv_list: List[str] = []
        self.total_comments = 0
    
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
                    'duration': data['data'].get('duration', 0),
                    'comment_count': data['data']['stat'].get('reply', 0),
                }
        except Exception as e:
            print(f"[-] 获取视频信息失败: {e}")
        return None
    
    def fetch_comments(self, aid: int, pages: int = MAX_PAGES) -> List[Dict]:
        """爬取评论 (25页)"""
        print(f"[*] 开始爬取评论，目标: {pages}页")
        
        all_comments = []
        
        for page in range(1, pages + 1):
            url = f"https://api.bilibili.com/x/v2/reply/main?type=1&oid={aid}&mode=0&pn={page}"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                data = response.json()
                
                if data['code'] != 0 or 'data' not in data:
                    break
                    
                if 'replies' not in data['data'] or not data['data']['replies']:
                    break
                
                replies = data['data']['replies']
                print(f"[+] 第{page}页获取到 {len(replies)} 条评论")
                
                for reply in replies:
                    content = reply['content']['message']
                    
                    # 跳过低质量评论
                    if PatternMatcher.is_low_quality(content):
                        continue
                    
                    comment_data = {
                        'rpid': str(reply['rpid']),
                        'content': content,
                        'like_count': reply.get('like', 0),
                        'reply_count': reply.get('rcount', 0),
                        'author': reply['member']['uname'],
                    }
                    
                    # 1. 检测AI总结 (高优先级)
                    ai_summary = PatternMatcher.extract_ai_summary(content)
                    if ai_summary:
                        self.ai_summaries.append(ai_summary)
                        print(f"  [AI总结] 发现AI总结: {ai_summary[:50]}...")
                        comment_data['is_ai_summary'] = True
                    
                    # 2. 检测求助请求 (高优先级)
                    help_requests = PatternMatcher.detect_help_requests(content)
                    if help_requests:
                        self.help_requests.append({
                            'comment_id': comment_data['rpid'],
                            'author': comment_data['author'],
                            'content': content,
                            'requests': help_requests,
                            'like_count': comment_data['like_count'],
                        })
                        print(f"  [求助] 发现求助请求: {content[:50]}...")
                    
                    # 3. 提取BV号
                    bvs = PatternMatcher.extract_bv_numbers(content)
                    if bvs:
                        self.priority_bv_list.extend(bvs)
                        comment_data['mentioned_bvs'] = bvs
                    
                    # 4. 提取时间标记
                    time_markers = PatternMatcher.extract_time_markers(content)
                    comment_data['time_markers'] = time_markers
                    
                    # 5. 提取故事名称
                    story_names = PatternMatcher.extract_story_names(content)
                    comment_data['mentioned_stories'] = story_names
                    
                    # 6. 检测规范格式
                    is_standard = PatternMatcher.is_standard_help_format(content)
                    comment_data['is_standard_format'] = is_standard
                    
                    # 7. 检测时间+故事组合
                    has_time_story = bool(time_markers) and PatternMatcher.has_story_content(content)
                    comment_data['has_time_story'] = has_time_story
                    
                    all_comments.append(comment_data)
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"[-] 第{page}页爬取异常: {e}")
                break
        
        self.total_comments = len(all_comments)
        print(f"[+] 评论爬取完成，共获取 {self.total_comments} 条有效评论")
        
        return all_comments
    
    def process_comments(self, comments: List[Dict], video_title: str, bvid: str):
        """处理评论并提取故事"""
        print("[*] 开始处理评论...")
        
        # 提取当前视频期数
        current_episode = ""
        episode_match = re.search(r'道听途说(\d+)', video_title)
        if episode_match:
            current_episode = f"道听途说{episode_match.group(1)}期"
        
        for comment in comments:
            content = comment['content']
            
            # 处理提及的往期故事
            for story_name in comment.get('mentioned_stories', []):
                if story_name != current_episode:
                    stats = self.story_stats[story_name]
                    stats['mention_count'] += 1
                    stats['bv_list'].update(comment.get('mentioned_bvs', []))
                    stats['time_markers'].update(comment.get('time_markers', []))
                    stats['comments'].append({
                        'content': content[:200],
                        'like_count': comment['like_count'],
                        'reply_count': comment['reply_count'],
                        'author': comment['author'],
                    })
                    
                    # 求助计数
                    if comment.get('is_standard_format'):
                        stats['standard_format_count'] += 1
                    if comment.get('has_time_story'):
                        stats['time_with_story_count'] += 1
            
            # 处理时间+故事组合 (当期故事)
            if comment.get('has_time_story') and not comment.get('mentioned_stories'):
                for marker in comment.get('time_markers', []):
                    story_key = f"当期故事_{marker}"
                    stats = self.story_stats[story_key]
                    stats['mention_count'] += 1
                    stats['time_markers'].add(marker)
                    stats['category'] = '当期'
                    stats['comments'].append({
                        'content': content[:200],
                        'like_count': comment['like_count'],
                        'reply_count': comment['reply_count'],
                        'author': comment['author'],
                    })
                    if comment.get('is_standard_format'):
                        stats['standard_format_count'] += 1
        
        print(f"[+] 故事提取完成，共发现 {len(self.story_stats)} 个故事")
    
    def run(self, bvid: str) -> Dict:
        """执行爬虫主流程"""
        print("=" * 60)
        print("怖客智能爬虫 V3.1 启动...")
        print(f"目标视频: {bvid}")
        print(f"爬取页数: {MAX_PAGES}页")
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
        comments = self.fetch_comments(video_info['aid'])
        
        if not comments:
            print("[-] 未获取到评论，退出...")
            return None
        
        # 3. 处理评论
        self.process_comments(comments, video_info['title'], bvid)
        
        # 4. 去重BV号
        self.priority_bv_list = list(set(self.priority_bv_list))
        
        # 5. 计算热度并生成结果
        stories = []
        for name, stats in self.story_stats.items():
            story_data = {
                'name': name,
                'mention_count': stats['mention_count'],
                'bv_list': list(stats['bv_list']),
                'time_markers': list(stats['time_markers']),
                'comments': stats['comments'][:10],
                'help_request_count': stats['help_request_count'],
                'standard_format_count': stats['standard_format_count'],
                'time_with_story_count': stats['time_with_story_count'],
                'category': stats['category'],
                'source_video': video_info['title'],
                'source_bvid': bvid,
            }
            story_data['heat_score'] = HeatScoreCalculator.calculate(story_data)
            stories.append(story_data)
        
        # 按热度排序
        stories.sort(key=lambda x: x['heat_score'], reverse=True)
        
        # 分类
        current_stories = [s for s in stories if s['category'] == '当期']
        past_stories = [s for s in stories if s['category'] == '往期']
        
        result = {
            'generated_at': datetime.now().isoformat(),
            'version': 'v3.1',
            'source_video': video_info['title'],
            'source_bvid': bvid,
            'ai_summaries': self.ai_summaries,
            'current_stories': current_stories,
            'past_stories': past_stories,
            'help_requests': self.help_requests[:30],
            'priority_bv_list': self.priority_bv_list,
            'total_comments': self.total_comments,
            'total_stories': len(stories),
        }
        
        print(f"\n{'='*60}")
        print(f"[+] 爬虫执行完毕!")
        print(f"[+] 总评论数: {self.total_comments}")
        print(f"[+] 当期故事: {len(current_stories)}个")
        print(f"[+] 往期故事: {len(past_stories)}个")
        print(f"[+] 求助请求: {len(self.help_requests)}条")
        print(f"[+] AI总结: {len(self.ai_summaries)}条")
        print(f"[+] 待爬取BV号: {len(self.priority_bv_list)}个")
        print(f"{'='*60}")
        
        return result


# ==========================================
# 主程序
# ==========================================

def main():
    """主函数"""
    # Cookie配置
    cookie = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; __itrace_wid=fd682858-9fa6-4ccb-28b2-a82e62ee6170; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3MDM3MDUsImlhdCI6MTc3MjQ0NDQ0NSwicGx0IjotMX0.jJ8uRdHhcV20bl1uTXzBZcP-obdgB7EFRArutjbbkXc; bili_ticket_expires=1772703645; SESSDATA=2472a2ba%2C1788001684%2C9597f%2A32CjCu75QuNog6ez4sRyS7UWd6z7Dz2bgwMqaehPf-a6TFPpB459i5lam46JdKNH0r0Z8SVjNEcTNPem5pV2k4ODg3cV9oU0RwWXFHdUlpbC0ydUZLRXdyRFJwMDZCMW5nNDZBRG5LZTJ1QzFLcXAyV29KTTNaelUxMHFkLU1KVFFramZkalFxMnpBIIEC; bili_jct=019f8b4045241197796aace28d79a311; sid=575k0iix; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bp_t_offset_16107971=1175944487818493952; CURRENT_FNVAL=4048; b_lsid=6DF899DC_19CB99459D0"
    
    # 初始化爬虫
    crawler = BilibiliCrawlerV31(cookie=cookie)
    
    # 目标BV号
    target_bvids = [
        "BV1Gg6iB9EbS",  # 【道听途说特辑】
        "BV1D1qpB6ECc",  # 【道听途说165上】
        "BV19SiFB1E1q",  # 【道听途说166下】
    ]
    
    # 爬取多个视频
    all_results = []
    for bvid in target_bvids:
        result = crawler.run(bvid)
        if result:
            all_results.append(result)
            with open(f'buke_v31_{bvid}.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 重置爬虫状态
        crawler = BilibiliCrawlerV31(cookie=cookie)
        time.sleep(2)
    
    # 合并结果
    if all_results:
        merged = {
            'generated_at': datetime.now().isoformat(),
            'version': 'v3.1',
            'total_videos': len(all_results),
            'results': all_results,
        }
        
        with open('buke_crawler_v31_merged.json', 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\n[+] 合并结果已保存")


if __name__ == "__main__":
    main()