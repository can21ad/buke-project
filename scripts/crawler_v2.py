import requests
import re
import json
import time
import random
from typing import List, Dict, Any, Tuple
from collections import Counter
from datetime import datetime

# ==========================================
# 怖客 (Buke) - B站视频评论区智能爬虫 V2
# ==========================================
# 改进版：标题相关性、表情包过滤、关键词提取、自动获取新BV号

class BilibiliCrawler:
    def __init__(self, cookie=''):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://www.bilibili.com',
            'Cookie': cookie if cookie else 'buvid3=default; buvid4=default'
        }
        self.time_pattern = re.compile(r'(\d{1,2}:\d{2})')
        
        # 表情包模式 - 过滤纯表情/颜文字评论
        self.emoji_pattern = re.compile(r'(\[.*?\]|[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F700-\U0001F77F]|[\U0001F780-\U0001F7FF]|[\U0001F800-\U0001F8FF]|[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|[\U0001FA70-\U0001FAFF]|[\u2600-\u26FF]|[\u2700-\u27BF]|\(.*?\)|（.*?）|www|哈哈|hhh|666|牛逼|卧槽|牛逼|太强了|绝了|好家伙|笑死|笑喷|哈哈哈哈|红红火火|恍恍惚惚)')
        
        # 故事相关关键词 - 增加权重
        self.story_keywords = [
            '故事', '经历', '真实', '灵异', '恐怖', '吓人', '诡异', '离奇',
            '那个', '这个', '后来', '当时', '晚上', '半夜', '凌晨', '深夜',
            '听到', '看到', '感觉', '发现', '遇到', '发生', '出现', '消失',
            '鬼', '魂', '灵', '怪', '妖', '魔', '神', '仙', '佛',
            '老人', '小孩', '女人', '男人', '朋友', '亲戚', '邻居', '家人',
            '房子', '房间', '楼', '村', '山', '水', '路', '车',
            '梦', '睡', '醒', '死', '活', '走', '来', '去'
        ]
        
        # 求出处/推荐关键词
        self.seek_keywords = ['求出处', '推荐', '那个故事', '第几个', '几分几秒', '原版', '来源', '在哪看', 'BV号']
        
        # 存储已处理的BV号
        self.processed_bvids = set()
        self.load_processed_bvids()

    def load_processed_bvids(self):
        """加载已处理的BV号"""
        try:
            with open('processed_bvids.json', 'r', encoding='utf-8') as f:
                self.processed_bvids = set(json.load(f))
        except:
            self.processed_bvids = set()

    def save_processed_bvids(self):
        """保存已处理的BV号"""
        with open('processed_bvids.json', 'w', encoding='utf-8') as f:
            json.dump(list(self.processed_bvids), f, ensure_ascii=False, indent=2)

    def get_latest_bvids(self, mid: str = '28346875', count: int = 10) -> List[str]:
        """从UP主投稿页面获取最新的BV号"""
        print(f"[*] 正在获取UP主 {mid} 的最新视频...")
        bvids = []
        
        # 方法1: 使用API获取
        api_url = f"https://api.bilibili.com/x/space/wbi/arc/search?mid={mid}&ps=30&tid=0&pn=1&order=pubdate"
        try:
            response = requests.get(api_url, headers=self.headers, timeout=15)
            data = response.json()
            if data['code'] == 0 and 'data' in data and 'list' in data['data']:
                vlist = data['data']['list']['vlist']
                for video in vlist:
                    bvid = video.get('bvid', '')
                    if bvid and bvid not in self.processed_bvids:
                        bvids.append(bvid)
                        print(f"  -> 发现新视频: {video.get('title', '')[:30]}... ({bvid})")
                        if len(bvids) >= count:
                            break
        except Exception as e:
            print(f"[-] API获取失败: {e}")
        
        # 如果API获取不足，使用备用方法
        if len(bvids) < count:
            print("[*] 尝试备用方法获取视频列表...")
            bvids.extend(self.get_bvids_from_page(mid, count - len(bvids)))
        
        return bvids[:count]

    def get_bvids_from_page(self, mid: str, count: int) -> List[str]:
        """从UP主空间页面解析BV号"""
        bvids = []
        url = f"https://space.bilibili.com/{mid}/upload/video"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            # 从页面源码中提取BV号
            found_bvids = re.findall(r'BV[a-zA-Z0-9]{10}', response.text)
            for bvid in found_bvids:
                if bvid not in self.processed_bvids and bvid not in bvids:
                    bvids.append(bvid)
                    if len(bvids) >= count:
                        break
        except Exception as e:
            print(f"[-] 页面解析失败: {e}")
        
        return bvids

    def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """获取视频信息"""
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            if data['code'] == 0:
                video_data = data['data']
                return {
                    'aid': video_data['aid'],
                    'title': video_data['title'],
                    'bvid': bvid,
                    'desc': video_data.get('desc', ''),
                    'duration': video_data.get('duration', 0),
                    'pub_date': video_data.get('pubdate', 0)
                }
            else:
                print(f"[-] 获取视频信息失败 {bvid}: {data['message']}")
        except Exception as e:
            print(f"[-] 请求异常: {e}")
        return None

    def time_to_seconds(self, time_str: str) -> int:
        """时间字符串转秒数"""
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0

    def extract_title_keywords(self, title: str) -> List[str]:
        """从标题中提取关键词"""
        # 移除特殊字符和数字
        clean_title = re.sub(r'[【】\[\]()（）\d]+', ' ', title)
        # 提取中文词组(2-6字)
        keywords = re.findall(r'[\u4e00-\u9fa5]{2,6}', clean_title)
        # 过滤常见无意义词
        stop_words = ['道听途说', '稍后', '再看', '更新', '本期', '视频', '内容', '分享']
        return [k for k in keywords if k not in stop_words and len(k) >= 2]

    def calculate_relevance_score(self, content: str, title_keywords: List[str]) -> float:
        """计算评论与标题的相关性得分"""
        score = 0.0
        content_lower = content.lower()
        
        for keyword in title_keywords:
            if keyword in content:
                score += 10.0  # 标题关键词匹配加分
        
        # 故事相关关键词匹配
        for kw in self.story_keywords:
            if kw in content:
                score += 2.0
        
        return score

    def is_low_quality_comment(self, content: str) -> bool:
        """判断是否为低质量评论(表情包/颜文字为主)"""
        # 移除表情和颜文字后的内容
        cleaned = self.emoji_pattern.sub('', content)
        cleaned = re.sub(r'\s+', '', cleaned)
        
        # 如果剩余内容少于10个字符，认为是低质量
        if len(cleaned) < 10:
            return True
        
        # 如果表情符号占比超过50%
        emoji_count = len(self.emoji_pattern.findall(content))
        if emoji_count > len(content) * 0.3:
            return True
        
        # 纯数字或纯符号
        if re.match(r'^[\d\s\.\,\!\?\!\?。！？，、]+$', content):
            return True
        
        return False

    def extract_keywords_from_comments(self, comments: List[Dict], title: str) -> Tuple[List[str], str]:
        """从评论中提取高频关键词，生成推荐主题"""
        all_words = []
        title_keywords = self.extract_title_keywords(title)
        
        for comment in comments:
            content = comment['review']
            # 提取中文词组
            words = re.findall(r'[\u4e00-\u9fa5]{2,6}', content)
            all_words.extend(words)
        
        # 统计词频
        word_freq = Counter(all_words)
        
        # 过滤停用词和标题词
        stop_words = {'这个', '那个', '就是', '不是', '没有', '什么', '怎么', '可以', '还是', '已经', '可能', '应该', '觉得', '感觉', '知道', '一下', '一个', '这种', '那样', '这样'}
        filtered_words = [(w, c) for w, c in word_freq.most_common(50) 
                         if w not in stop_words and len(w) >= 2 and c >= 2]
        
        # 取前10个高频词
        top_keywords = [w for w, c in filtered_words[:10]]
        
        # 生成推荐主题
        if top_keywords:
            theme = f"【{title_keywords[0] if title_keywords else '热门'}】" + '、'.join(top_keywords[:3])
        else:
            theme = f"【{title_keywords[0] if title_keywords else '精选'}】网友热议故事"
        
        return top_keywords, theme

    def fetch_hot_comments(self, aid: int, title: str, max_pages: int = 15) -> List[Dict]:
        """抓取并筛选高质量评论"""
        extracted_stories = []
        title_keywords = self.extract_title_keywords(title)
        
        for page in range(1, max_pages + 1):
            url = f"https://api.bilibili.com/x/v2/reply/main?type=1&oid={aid}&mode=2&pn={page}"
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                data = response.json()
                
                if data['code'] != 0 or 'data' not in data or not data['data']:
                    break
                if 'replies' not in data['data'] or not data['data']['replies']:
                    break
                
                print(f"[*] 第{page}页获取到 {len(data['data']['replies'])} 条评论")
                    
                replies = data['data']['replies']
                for reply in replies:
                    content = reply['content']['message']
                    like_count = reply['like']
                    
                    # 跳过低质量评论
                    if self.is_low_quality_comment(content):
                        continue
                    
                    content_length = len(content)
                    
                    # 必须满足以下条件之一
                    timestamps = self.time_pattern.findall(content)
                    has_timestamp = bool(timestamps)
                    has_story_content = content_length > 50  # 降低字数要求
                    has_seek_keyword = any(kw in content for kw in self.seek_keywords)
                    has_story_keyword = any(kw in content for kw in self.story_keywords[:10])  # 故事关键词
                    
                    if not (has_timestamp or has_story_content or has_seek_keyword or has_story_keyword):
                        continue
                    
                    # 计算相关性得分
                    relevance_score = self.calculate_relevance_score(content, title_keywords)
                    
                    timestamp_str = timestamps[0] if timestamps else '00:00'
                    
                    extracted_stories.append({
                        'timestamp_str': timestamp_str,
                        'timestamp_sec': self.time_to_seconds(timestamp_str),
                        'review': content.replace('\n', ' ').strip(),
                        'heat': like_count,
                        'length': content_length,
                        'relevance': relevance_score,
                        'has_timestamp': has_timestamp
                    })
                        
                time.sleep(0.3)
            except Exception as e:
                print(f"[-] 抓取评论异常: {e}")
                break
                
        return extracted_stories

    def calculate_score(self, item: Dict, noun_freq: Counter, title_keywords: List[str]) -> float:
        """计算评论综合得分 - 优化版"""
        # 1. 相关性得分 (权重最高)
        relevance_score = item.get('relevance', 0) * 3
        
        # 2. 内容质量得分
        length_score = min(item.get('length', 0) * 0.5, 100)  # 字数得分，上限100
        
        # 3. 时间戳得分 (有具体时间点很重要)
        timestamp_score = 300 if item.get('has_timestamp', False) else 0
        
        # 4. 热度得分 (降低权重)
        heat_score = min(item['heat'] * 0.05, 50)  # 点赞得分，上限50
        
        # 5. 名词频率得分
        nouns = re.findall(r'[\u4e00-\u9fa5]{2,4}', item['review'])
        noun_score = sum(noun_freq.get(n, 0) * 5 for n in nouns if noun_freq.get(n, 0) > 1)
        
        # 6. 求出处/推荐关键词加分
        seek_score = 200 if any(kw in item['review'] for kw in self.seek_keywords) else 0
        
        return relevance_score + length_score + timestamp_score + heat_score + noun_score + seek_score

    def run(self, bvid_list: List[str] = None, auto_fetch: bool = True, top_n: int = 50):
        """执行主抓取流程"""
        print("=" * 60)
        print("怖客智能爬虫 V2.0 启动...")
        print(f"目标: 提取 Top {top_n} 高质量故事")
        print("=" * 60)
        
        # 自动获取最新BV号
        if auto_fetch and not bvid_list:
            bvid_list = self.get_latest_bvids(count=5)
        
        if not bvid_list:
            print("[-] 没有可用的BV号，退出...")
            return
        
        print(f"\n[*] 本次将处理 {len(bvid_list)} 个视频:")
        for i, bvid in enumerate(bvid_list, 1):
            print(f"    {i}. {bvid}")
        
        seen_reviews = set()
        all_extracted_data = []
        video_titles = {}

        for bvid in bvid_list:
            print(f"\n{'='*50}")
            print(f"[*] 正在解析视频: {bvid}")
            
            v_info = self.get_video_info(bvid)
            if not v_info:
                continue
            
            video_titles[bvid] = v_info['title']
            print(f"[+] 视频标题: {v_info['title']}")
            print(f"[+] 视频时长: {v_info['duration']//60}分钟")
            print("[*] 正在挖掘评论区高质量故事...")
            
            stories = self.fetch_hot_comments(v_info['aid'], v_info['title'])
            
            for story in stories:
                # 去重
                review_key = story['review'][:50]
                if review_key in seen_reviews:
                    continue
                seen_reviews.add(review_key)
                
                # 提取标签
                tags = self.extract_tags(story['review'], v_info['title'])
                
                item = {
                    'title': v_info['title'],
                    'bvid': bvid,
                    'timestamp': story['timestamp_sec'],
                    'heat': story['heat'],
                    'review': story['review'],
                    'length': story['length'],
                    'author': '@大佬何金银',
                    'tags': tags,
                    'relevance': story.get('relevance', 0)
                }
                all_extracted_data.append(item)
                print(f"  -> [{story['timestamp_str']}] 字数:{story['length']} 点赞:{story['heat']} | {story['review'][:40]}...")

            # 标记为已处理
            self.processed_bvids.add(bvid)
            time.sleep(1)

        if not all_extracted_data:
            print("\n[-] 未提取到任何数据")
            return

        # 统计名词频率
        all_nouns = []
        for item in all_extracted_data:
            all_nouns.extend(re.findall(r'[\u4e00-\u9fa5]{2,4}', item['review']))
        noun_freq = Counter(all_nouns)

        # 提取全局关键词和主题
        global_keywords, global_theme = self.extract_keywords_from_comments(all_extracted_data, list(video_titles.values())[0] if video_titles else '')
        
        print(f"\n[*] 全局高频关键词: {', '.join(global_keywords[:10])}")
        print(f"[*] 推荐主题: {global_theme}")

        # 计算综合得分并排序
        for item in all_extracted_data:
            title_keywords = self.extract_title_keywords(item['title'])
            item['final_score'] = self.calculate_score(item, noun_freq, title_keywords)
        
        top_stories = sorted(all_extracted_data, key=lambda x: x['final_score'], reverse=True)[:top_n]

        # 为每个故事生成推荐标题
        for i, story in enumerate(top_stories, 1):
            story['rank'] = i
            story['recommend_title'] = self.generate_recommend_title(story, global_keywords)

        # 保存结果
        output_file = 'buke_top_stories.json'
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'total_extracted': len(all_extracted_data),
            'top_n': top_n,
            'theme': global_theme,
            'keywords': global_keywords[:10],
            'stories': top_stories
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 保存已处理的BV号
        self.save_processed_bvids()
        
        print(f"\n{'='*60}")
        print(f"[+] 爬虫执行完毕！")
        print(f"[+] 从 {len(bvid_list)} 个视频中提取了 {len(all_extracted_data)} 条评论")
        print(f"[+] 筛选出 Top {len(top_stories)} 高质量故事")
        print(f"[+] 数据已保存至: {output_file}")
        print(f"{'='*60}")

    def extract_tags(self, content: str, title: str) -> List[str]:
        """从内容和标题中提取标签"""
        tags = []
        
        # 从标题提取
        title_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', title)
        tags.extend(title_words[:2])
        
        # 检测故事类型
        type_keywords = {
            '灵异': ['鬼', '魂', '灵', '诡异', '恐怖'],
            '真实经历': ['亲身', '经历', '真实', '发生'],
            '民间传说': ['传说', '故事', '老人', '村里'],
            '细思极恐': ['细思', '后怕', '细想'],
            '都市传说': ['城市', '都市', '现代']
        }
        
        for tag, keywords in type_keywords.items():
            if any(kw in content or kw in title for kw in keywords):
                tags.append(tag)
        
        # 去重并限制数量
        tags = list(dict.fromkeys(tags))[:4]
        
        if not tags:
            tags = ['热门故事', '网友推荐']
        
        return tags

    def generate_recommend_title(self, story: Dict, global_keywords: List[str]) -> str:
        """生成推荐标题"""
        title = story['title']
        review = story['review']
        
        # 尝试从评论中提取关键句
        sentences = re.split(r'[。！？，]', review)
        for sentence in sentences:
            if len(sentence) > 10 and any(kw in sentence for kw in global_keywords[:5]):
                return sentence[:50] + ('...' if len(sentence) > 50 else '')
        
        # 使用原标题的关键词
        title_keywords = self.extract_title_keywords(title)
        if title_keywords:
            return f"【{title_keywords[0]}】相关故事"
        
        return "精彩故事片段"


if __name__ == "__main__":
    # Cookie配置 (必须填写)
    cookie = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; __itrace_wid=fd682858-9fa6-4ccb-28b2-a82e62ee6170; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3MDM3MDUsImlhdCI6MTc3MjQ0NDQ0NSwicGx0IjotMX0.jJ8uRdHhcV20bl1uTXzBZcP-obdgB7EFRArutjbbkXc; bili_ticket_expires=1772703645; SESSDATA=2472a2ba%2C1788001684%2C9597f%2A32CjCu75QuNog6ez4sRyS7UWd6z7Dz2bgwMqaehPf-a6TFPpB459i5lam46JdKNH0r0Z8SVjNEcTNPem5pV2k4ODg3cV9oU0RwWXFHdUlpbC0ydUZLRXdyRFJwMDZCMW5nNDZBRG5LZTJ1QzFLcXAyV29KTTNaelUxMHFkLU1KVFFramZkalFxMnpBIIEC; bili_jct=019f8b4045241197796aace28d79a311; sid=575k0iix; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bp_t_offset_16107971=1175944487818493952; CURRENT_FNVAL=4048; b_lsid=6DF899DC_19CB99459D0"
    
    spider = BilibiliCrawler(cookie=cookie)
    
    # 手动指定最新的BV号列表 (大佬何金银最新视频)
    # 每次运行会自动更换3个新BV号
    target_bvids = [
        "BV1Gg6iB9EbS",  # 【道听途说特辑】三小时
        "BV1D1qpB6ECc",  # 【道听途说165上】乐山外卖员
        "BV19SiFB1E1q",  # 【道听途说166下】恐怖老人
        "BV1vh3gzwE4H",  # 【道听途说153】表姐中邪
        "BV1MLTxz9EZE",  # 【道听途说151上】二奶奶
        "BV1xx411c7mD",  # 字幕君交流场所
        "BV1xx411c7mE",  # 其他视频
    ]
    
    # 运行爬虫，筛选Top 50高质量故事
    spider.run(bvid_list=target_bvids, auto_fetch=False, top_n=50)