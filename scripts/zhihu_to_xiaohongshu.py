#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎回答爬取与分析工具
用于爬取用户知乎回答并生成小红书文案
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from datetime import datetime
from typing import List, Dict

class ZhihuAnswerAnalyzer:
    """知乎回答分析器"""
    
    def __init__(self):
        self.answers = []
    
    def add_answer(self, answer_data: Dict):
        """添加回答数据"""
        self.answers.append(answer_data)
    
    def sort_by_votes(self) -> List[Dict]:
        """按赞同数排序"""
        return sorted(self.answers, key=lambda x: x.get('votes', 0), reverse=True)
    
    def analyze_content_style(self) -> Dict:
        """分析内容风格"""
        analysis = {
            'total_answers': len(self.answers),
            'total_votes': sum(a.get('votes', 0) for a in self.answers),
            'avg_votes': sum(a.get('votes', 0) for a in self.answers) / len(self.answers) if self.answers else 0,
            'topics': [],
            'style_keywords': []
        }
        return analysis
    
    def generate_xiaohongshu_content(self, answer: Dict, style: str = 'controversial') -> str:
        """
        生成小红书文案
        
        Args:
            answer: 回答数据
            style: 风格 - 'controversial'(争议性), 'gentle'(温和), 'dry_goods'(干货)
        """
        title = answer.get('title', '')
        content = answer.get('content', '')
        votes = answer.get('votes', 0)
        
        if style == 'controversial':
            # 争议性风格 - 适合起号
            template = f"""💥 {title[:20]}...

姐妹们，今天看到一个观点真的让我破防了😤

{content[:150]}...

说实话，这个观点真的很有争议，但我不得不说...

✨ 核心观点：
{self._extract_key_points(content)}

你们觉得呢？评论区聊聊👇

#观点分享 #深度思考 #社会观察 #女生必看 #独立思考"""
        
        elif style == 'gentle':
            # 温和风格
            template = f"""🌸 {title[:20]}...

今天想和大家聊聊这个话题💭

{content[:150]}...

💡 我的看法：
{self._extract_key_points(content)}

希望姐妹们都能有自己的思考✨

#女性成长 #独立思考 #观点分享"""
        
        else:  # dry_goods
            # 干货风格
            template = f"""📚 {title[:20]}...

干货预警！今天分享一个深度观点👇

{content[:200]}...

🔥 重点总结：
{self._extract_key_points(content)}

收藏起来慢慢看！

#干货分享 #深度内容 #知识分享"""
        
        return template
    
    def _extract_key_points(self, content: str, num_points: int = 3) -> str:
        """提取关键观点"""
        # 简单实现 - 按句子分割并取前几句
        sentences = content.split('。')
        key_points = []
        for i, sent in enumerate(sentences[:num_points]):
            if sent.strip():
                key_points.append(f"{i+1}. {sent.strip()}")
        return '\n'.join(key_points)
    
    def save_to_json(self, filepath: str):
        """保存数据到JSON"""
        data = {
            'crawled_at': datetime.now().isoformat(),
            'total_answers': len(self.answers),
            'answers': self.answers
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 数据已保存: {filepath}")

# 示例数据 - 已爬取的高赞回答
SAMPLE_ANSWERS = [
    {
        'title': '如何评价电视剧《以法之名》大结局？',
        'votes': 162,
        'content': '洪亮是舒服了，案子一结束家破人亡，估计还要妻离子散，工作由于枪击案和谢鸿飞大概率也是没了，至少停职很久。好朋友因为他要么死，要么停职要么调职，心里巴不得恨死这个犟种了。要保护的证人一个没留住，该死的全死，做出的承诺和放屁没区别。自己爸妈没了自己所谓检察官的这服皮囊，在村里依旧不会多被看得起。结局洪亮赢了，正义必胜，法律必胜，所以这样值得么，哦不应该是对洪亮来说值得么？现实中为了追求绝对正义而不惜大义灭亲的那个洪亮，绝对不可能有机会活着从江家的门口走出来，江旭东不会允许，禹天成更不会。到最后反而成了"中国检察官"一样的爽剧，真的让人很恶心。或者说导演是在说"看好了，这就是伸张正义的下场，你以为你赢了么？"这样看，就很符合剧意。',
        'url': 'https://www.zhihu.com/question/1926027915935581284/answer/1926447726385673759'
    },
    {
        'title': '如何看待赵朔西行漫记最新一期视频公布小猫悟空的死因？',
        'votes': 117,
        'content': '最经典的中式结局，也是意料之中。老套的手法，老套的公关，笨拙的解释以及一个荒唐的结局。这就是当地部门交出来的答卷。但互联网确实没有记忆，现在赵朔账号私密了，等这破事冷几个月，又是无事发生。你能做什么？你又能改变什么？你连一只猫的死因都不配知道。这才是真正的课堂不是么。',
        'url': 'https://www.zhihu.com/question/1904275971659498966/answer/1904351745901049343'
    },
    {
        'title': '如何看待睡前消息第858期《我的中美"对账" 从1984开始》？',
        'votes': 130,
        'content': '太悲哀了，真的太悲哀了。马督工现在已经在bu那里和户子，峰哥放一块了。你让我想破脑袋我也想不到这三个人除了性别相同影响力大一点以外还有什么相似点。在贴吧和你b，现在的一些人已经完全不加掩饰的承认自己是极右还沾沾自喜了，你们知道从你们嘴里说出来崇拜某某，怀念某某是十分荒唐可笑的么。',
        'url': 'https://www.zhihu.com/question/10779863237/answer/89229409105'
    },
    {
        'title': '为什么官方要叫停外卖大战？',
        'votes': 91,
        'content': '市场又一次对于消费者的最好诠释，竞争能带来什么，垄断又能带来什么。老百姓是用神卷大小投票的，而不是被哄骗被蒙眼。确实时间拉长，这种程度的烧钱是不可持续的，但很多领域的巨头能不花一分钱就拿下大头的市场占额，高枕无忧几十年，是不是更可笑呢。',
        'url': 'https://www.zhihu.com/question/1930186114603384929/answer/1932014890681337030'
    }
]

def main():
    """主函数"""
    print("=" * 60)
    print("知乎回答分析 - 小红书文案生成器")
    print("=" * 60)
    
    analyzer = ZhihuAnswerAnalyzer()
    
    # 添加示例数据
    for answer in SAMPLE_ANSWERS:
        analyzer.add_answer(answer)
    
    # 按赞同数排序
    sorted_answers = analyzer.sort_by_votes()
    
    print(f"\n📊 数据概览:")
    print(f"   总回答数: {len(sorted_answers)}")
    print(f"   总赞同数: {sum(a['votes'] for a in sorted_answers)}")
    print(f"   平均赞同: {sum(a['votes'] for a in sorted_answers) / len(sorted_answers):.1f}")
    
    print(f"\n🏆 高赞回答 TOP {len(sorted_answers)}:")
    for i, ans in enumerate(sorted_answers, 1):
        print(f"   {i}. {ans['title'][:30]}... ({ans['votes']}赞同)")
    
    # 生成小红书文案
    print(f"\n📝 生成小红书文案 (争议性风格 - 适合起号):")
    print("=" * 60)
    
    for i, ans in enumerate(sorted_answers[:3], 1):
        xhs_content = analyzer.generate_xiaohongshu_content(ans, style='controversial')
        print(f"\n--- 文案 {i} ---")
        print(xhs_content)
        print("\n" + "=" * 60)
    
    # 保存数据
    output_path = os.path.join(os.path.dirname(__file__), 'zhihu_answers_analysis.json')
    analyzer.save_to_json(output_path)
    
    print(f"\n✅ 分析完成！")
    print(f"   数据文件: {output_path}")
    print(f"   建议: 这些文案可以直接复制到小红书发布")

if __name__ == "__main__":
    main()