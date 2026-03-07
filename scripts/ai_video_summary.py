#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - AI视频总结插件
==========================================
使用B站内置AI总结功能获取视频内容总结
"""

import requests
import re
import json
import time
from typing import Dict, Optional, List
from datetime import datetime


class BilibiliAISummary:
    """B站AI视频总结"""
    
    def __init__(self, cookie: str = ''):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://www.bilibili.com',
            'Cookie': cookie if cookie else 'buvid3=default; buvid4=default'
        }
    
    def get_video_info(self, bvid: str) -> Optional[Dict]:
        """获取视频基本信息"""
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            data = response.json()
            if data['code'] == 0:
                return {
                    'aid': data['data']['aid'],
                    'cid': data['data']['cid'],
                    'title': data['data']['title'],
                    'bvid': bvid,
                    'duration': data['data'].get('duration', 0),
                    'desc': data['data'].get('desc', ''),
                    'owner': data['data']['owner']['name'],
                    'view_count': data['data']['stat'].get('view', 0),
                }
        except Exception as e:
            print(f"[-] 获取视频信息失败: {e}")
        return None
    
    def get_ai_summary(self, bvid: str) -> Optional[Dict]:
        """
        获取AI视频总结
        
        B站AI总结API:
        - 需要登录状态
        - 使用视频的aid和cid
        """
        print(f"[*] 正在获取视频 {bvid} 的AI总结...")
        
        # 1. 获取视频信息
        video_info = self.get_video_info(bvid)
        if not video_info:
            return None
        
        aid = video_info['aid']
        cid = video_info['cid']
        
        # 2. 尝试获取AI总结 (B站内置功能)
        # API端点: https://api.bilibili.com/x/web-interface/view/conclusion/get
        summary_url = "https://api.bilibili.com/x/web-interface/view/conclusion/get"
        params = {
            'bvid': bvid,
            'cid': cid,
            'up_mid': 0,  # UP主ID
            'is_detailed': 1,  # 获取详细总结
        }
        
        try:
            response = requests.get(summary_url, headers=self.headers, params=params, timeout=30)
            data = response.json()
            
            if data['code'] == 0 and 'data' in data and data['data']:
                summary_data = data['data']
                
                result = {
                    'bvid': bvid,
                    'title': video_info['title'],
                    'owner': video_info['owner'],
                    'duration': video_info['duration'],
                    'ai_summary': {
                        'model_result': summary_data.get('model_result', ''),
                        'summary': summary_data.get('summary', ''),
                        'outline': summary_data.get('outline', []),
                        'keywords': summary_data.get('keywords', []),
                    },
                    'generated_at': datetime.now().isoformat(),
                }
                
                print(f"[+] AI总结获取成功!")
                return result
            else:
                print(f"[-] AI总结暂不可用: {data.get('message', '未知原因')}")
                
        except Exception as e:
            print(f"[-] 获取AI总结失败: {e}")
        
        # 3. 如果AI总结不可用，尝试从字幕生成总结
        return self.get_subtitle_summary(bvid, video_info)
    
    def get_subtitle_summary(self, bvid: str, video_info: Dict) -> Optional[Dict]:
        """从字幕生成总结"""
        print(f"[*] 尝试从字幕生成总结...")
        
        aid = video_info['aid']
        cid = video_info['cid']
        
        # 获取字幕列表
        subtitle_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        
        try:
            response = requests.get(subtitle_url, headers=self.headers, timeout=15)
            data = response.json()
            
            if data['code'] == 0 and 'data' in data:
                subtitle_info = data['data'].get('subtitle', {})
                subtitles = subtitle_info.get('subtitles', [])
                
                if subtitles:
                    # 获取第一个字幕
                    subtitle_url = subtitles[0].get('subtitle_url', '')
                    if subtitle_url:
                        if not subtitle_url.startswith('http'):
                            subtitle_url = 'https:' + subtitle_url
                        
                        # 获取字幕内容
                        subtitle_response = requests.get(subtitle_url, timeout=15)
                        subtitle_data = subtitle_response.json()
                        
                        # 提取文本
                        texts = []
                        for item in subtitle_data.get('body', []):
                            texts.append(item.get('content', ''))
                        
                        full_text = ' '.join(texts)
                        
                        # 生成简单总结
                        summary = self._generate_simple_summary(full_text, video_info['title'])
                        
                        result = {
                            'bvid': bvid,
                            'title': video_info['title'],
                            'owner': video_info['owner'],
                            'duration': video_info['duration'],
                            'ai_summary': {
                                'model_result': summary,
                                'summary': summary[:500] + '...' if len(summary) > 500 else summary,
                                'outline': [],
                                'keywords': self._extract_keywords(full_text),
                                'source': 'subtitle',
                            },
                            'generated_at': datetime.now().isoformat(),
                        }
                        
                        print(f"[+] 字幕总结生成成功!")
                        return result
                        
        except Exception as e:
            print(f"[-] 字幕获取失败: {e}")
        
        # 4. 如果都没有，返回视频描述作为总结
        return {
            'bvid': bvid,
            'title': video_info['title'],
            'owner': video_info['owner'],
            'duration': video_info['duration'],
            'ai_summary': {
                'model_result': video_info.get('desc', '暂无总结'),
                'summary': video_info.get('desc', '暂无总结')[:500],
                'outline': [],
                'keywords': [],
                'source': 'description',
            },
            'generated_at': datetime.now().isoformat(),
        }
    
    def _generate_simple_summary(self, text: str, title: str) -> str:
        """生成简单总结"""
        # 提取关键句子
        sentences = re.split(r'[。！？]', text)
        
        # 取前10个有意义的句子
        key_sentences = []
        for s in sentences:
            s = s.strip()
            if len(s) > 10 and len(s) < 100:
                key_sentences.append(s)
            if len(key_sentences) >= 10:
                break
        
        summary = f"【{title}】\n\n主要内容：\n" + '\n'.join(f"• {s}" for s in key_sentences)
        return summary
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []
        
        # 故事相关关键词
        story_keywords = [
            '故事', '经历', '真实', '灵异', '恐怖', '诡异', '离奇',
            '鬼', '魂', '灵', '怪', '妖', '魔', '神', '仙',
            '老人', '小孩', '女人', '男人', '朋友', '亲戚',
        ]
        
        for kw in story_keywords:
            if kw in text and kw not in keywords:
                keywords.append(kw)
        
        return keywords[:10]
    
    def batch_summarize(self, bvid_list: List[str], output_file: str = 'ai_summaries.json') -> List[Dict]:
        """批量获取AI总结"""
        print(f"[*] 开始批量获取 {len(bvid_list)} 个视频的AI总结...")
        
        results = []
        for i, bvid in enumerate(bvid_list, 1):
            print(f"\n[{i}/{len(bvid_list)}] 处理: {bvid}")
            
            summary = self.get_ai_summary(bvid)
            if summary:
                results.append(summary)
            
            time.sleep(1)  # 避免请求过快
        
        # 保存结果
        output = {
            'generated_at': datetime.now().isoformat(),
            'total_videos': len(bvid_list),
            'success_count': len(results),
            'summaries': results,
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n[+] 批量总结完成，成功 {len(results)}/{len(bvid_list)} 个")
        print(f"[+] 结果已保存至: {output_file}")
        
        return results


def main():
    """主函数"""
    # Cookie配置 (需要登录状态才能使用AI总结)
    cookie = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; __itrace_wid=fd682858-9fa6-4ccb-28b2-a82e62ee6170; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3MDM3MDUsImlhdCI6MTc3MjQ0NDQ0NSwicGx0IjotMX0.jJ8uRdHhcV20bl1uTXzBZcP-obdgB7EFRArutjbbkXc; bili_ticket_expires=1772703645; SESSDATA=2472a2ba%2C1788001684%2C9597f%2A32CjCu75QuNog6ez4sRyS7UWd6z7Dz2bgwMqaehPf-a6TFPpB459i5lam46JdKNH0r0Z8SVjNEcTNPem5pV2k4ODg3cV9oU0RwWXFHdUlpbC0ydUZLRXdyRFJwMDZCMW5nNDZBRG5LZTJ1QzFLcXAyV29KTTNaelUxMHFkLU1KVFFramZkalFxMnpBIIEC; bili_jct=019f8b4045241197796aace28d79a311; sid=575k0iix; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bp_t_offset_16107971=1175944487818493952; CURRENT_FNVAL=4048; b_lsid=6DF899DC_19CB99459D0"
    
    ai_summary = BilibiliAISummary(cookie=cookie)
    
    # 测试BV号
    test_bvids = [
        "BV1Gg6iB9EbS",  # 道听途说特辑
        "BV1D1qpB6ECc",  # 道听途说165上
        "BV19SiFB1E1q",  # 道听途说166下
    ]
    
    # 批量获取AI总结
    results = ai_summary.batch_summarize(test_bvids, 'ai_summaries.json')
    
    # 打印结果
    print("\n" + "="*60)
    print("AI总结结果:")
    print("="*60)
    for r in results:
        print(f"\n【{r['title']}】")
        print(f"BV号: {r['bvid']}")
        print(f"时长: {r['duration']//60}分钟")
        print(f"总结: {r['ai_summary']['summary'][:200]}...")


if __name__ == "__main__":
    main()