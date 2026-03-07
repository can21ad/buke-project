#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - BV号爬虫 V4
==========================================
使用公开API获取BV号
"""

import requests
import json
import time
import re
from typing import List, Dict
from datetime import datetime


class BVBilibiliCrawlerV4:
    """BV号爬虫 - 使用公开API"""
    
    def __init__(self, cookie: str = ''):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': cookie
        }
        self.session.headers.update(self.headers)
    
    def get_video_count(self, mid: str) -> int:
        """获取UP主视频总数"""
        url = f"https://api.bilibili.com/x/space/acc/info?mid={mid}"
        try:
            resp = self.session.get(url, timeout=10)
            data = resp.json()
            if data.get('code') == 0:
                return data.get('data', {}).get('archive_count', 0)
        except:
            pass
        return 0
    
    def get_bvids_search(self, mid: str = '28346875', max_pages: int = 50) -> List[Dict]:
        """方法1: 使用搜索API"""
        print(f"[*] 方法1: 使用搜索API获取视频列表...")
        
        all_videos = []
        page = 1
        
        while page <= max_pages:
            url = "https://api.bilibili.com/x/space/search/video"
            params = {
                'mid': mid,
                'pn': page,
                'ps': 30,
                'order': 'pubdate',
                'keyword': '',
                'jsonp': 'jsonp'
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=15)
                data = resp.json()
                
                if data.get('code') != 0:
                    print(f"[-] 搜索API错误: {data.get('message')}")
                    return all_videos
                
                vlist = data.get('data', {}).get('list', {}).get('vlist', [])
                if not vlist:
                    break
                
                for v in vlist:
                    all_videos.append({
                        'bvid': v.get('bvid'),
                        'aid': v.get('aid'),
                        'title': v.get('title'),
                        'play_count': v.get('play'),
                        'comment_count': v.get('comment'),
                        'pub_date': v.get('created'),
                        'duration': v.get('length'),
                        'pic': v.get('pic')
                    })
                    print(f"  [{len(all_videos)}] {v.get('bvid')}: {v.get('title', '')[:40]}...")
                
                if len(vlist) < 30:
                    break
                    
                page += 1
                time.sleep(0.3)
                
            except Exception as e:
                print(f"[-] 搜索API失败: {e}")
                break
        
        return all_videos
    
    def get_bvids_arc_search(self, mid: str = '28346875', max_pages: int = 50) -> List[Dict]:
        """方法2: 使用arc/search API"""
        print(f"[*] 方法2: 使用arc/search API获取视频列表...")
        
        all_videos = []
        page = 1
        
        while page <= max_pages:
            url = "https://api.bilibili.com/x/space/arc/search"
            params = {
                'mid': mid,
                'pn': page,
                'ps': 50,
                'tid': 0,
                'order': 'pubdate',
                'jsonp': 'jsonp'
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=15)
                data = resp.json()
                
                if data.get('code') != 0:
                    print(f"[-] arc/search API错误: {data.get('message')} (code: {data.get('code')})")
                    return all_videos
                
                vlist = data.get('data', {}).get('list', {}).get('vlist', [])
                if not vlist:
                    break
                
                for v in vlist:
                    all_videos.append({
                        'bvid': v.get('bvid'),
                        'aid': v.get('aid'),
                        'title': v.get('title'),
                        'play_count': v.get('play'),
                        'comment_count': v.get('comment'),
                        'pub_date': v.get('created'),
                        'duration': v.get('length'),
                        'pic': v.get('pic')
                    })
                    print(f"  [{len(all_videos)}] {v.get('bvid')}: {v.get('title', '')[:40]}...")
                
                count = data.get('data', {}).get('page', {}).get('count', 0)
                if len(all_videos) >= count:
                    print(f"[*] 已获取全部 {count} 个视频")
                    break
                
                if len(vlist) < 50:
                    break
                    
                page += 1
                time.sleep(0.3)
                
            except Exception as e:
                print(f"[-] arc/search API失败: {e}")
                break
        
        return all_videos
    
    def get_bvids_channel(self, mid: str = '28346875') -> List[Dict]:
        """方法3: 使用channel API"""
        print(f"[*] 方法3: 使用channel API获取视频列表...")
        
        all_videos = []
        
        url = f"https://api.bilibili.com/x/space/channel/video"
        params = {
            'mid': mid,
            'cid': 0,
            'pn': 1,
            'ps': 100
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=15)
            data = resp.json()
            
            if data.get('code') == 0:
                vlist = data.get('data', {}).get('list', {}).get('vlist', [])
                for v in vlist:
                    all_videos.append({
                        'bvid': v.get('bvid'),
                        'title': v.get('title'),
                    })
                    print(f"  [{len(all_videos)}] {v.get('bvid')}: {v.get('title', '')[:40]}...")
        except Exception as e:
            print(f"[-] channel API失败: {e}")
        
        return all_videos
    
    def get_bvids_web_interface(self, mid: str = '28346875', max_pages: int = 50) -> List[Dict]:
        """方法4: 使用web-interface API"""
        print(f"[*] 方法4: 使用web-interface API获取视频列表...")
        
        all_videos = []
        page = 1
        
        while page <= max_pages:
            url = "https://api.bilibili.com/x/web-interface/space"
            params = {
                'mid': mid,
                'pn': page,
                'ps': 50,
                'tid': 0,
                'order': 'pubdate',
                'keyword': '',
                'jsonp': 'jsonp'
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=15)
                data = resp.json()
                
                if data.get('code') != 0:
                    print(f"[-] web-interface API错误: {data.get('message')}")
                    return all_videos
                
                vlist = data.get('data', {}).get('list', {}).get('vlist', [])
                if not vlist:
                    break
                
                for v in vlist:
                    all_videos.append({
                        'bvid': v.get('bvid'),
                        'aid': v.get('aid'),
                        'title': v.get('title'),
                        'play_count': v.get('play'),
                        'comment_count': v.get('comment'),
                        'pub_date': v.get('created'),
                        'duration': v.get('length'),
                        'pic': v.get('pic')
                    })
                    print(f"  [{len(all_videos)}] {v.get('bvid')}: {v.get('title', '')[:40]}...")
                
                if len(vlist) < 50:
                    break
                    
                page += 1
                time.sleep(0.3)
                
            except Exception as e:
                print(f"[-] web-interface API失败: {e}")
                break
        
        return all_videos
    
    def get_all_bvids(self, mid: str = '28346875', max_pages: int = 50) -> List[Dict]:
        """尝试所有方法获取BV号"""
        
        total = self.get_video_count(mid)
        print(f"[*] UP主 {mid} 共有约 {total} 个视频")
        
        methods = [
            ('arc_search', self.get_bvids_arc_search),
            ('search', self.get_bvids_search),
            ('web_interface', self.get_bvids_web_interface),
        ]
        
        for name, method in methods:
            videos = method(mid, max_pages)
            if videos:
                return videos
        
        print("[-] 所有API方法都失败了")
        return []
    
    def save_bvids(self, videos: List[Dict], output_file: str = 'bilibili_bvids.json'):
        """保存BV号列表"""
        result = {
            'generated_at': datetime.now().isoformat(),
            'total_videos': len(videos),
            'source': 'https://space.bilibili.com/28346875/upload/video',
            'videos': videos,
            'bvid_list': [v['bvid'] for v in videos],
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[+] BV号列表已保存至: {output_file}")
        return result


def main():
    """主函数"""
    cookie = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; __itrace_wid=fd682858-9fa6-4ccb-28b2-a82e62ee6170; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3MDM3MDUsImlhdCI6MTc3MjQ0NDQ0NSwicGx0IjotMX0.jJ8uRdHhcV20bl1uTXzBZcP-obdgB7EFRArutjbbkXc; bili_ticket_expires=1772703645; SESSDATA=2472a2ba%2C1788001684%2C9597f%2A32CjCu75QuNog6ez4sRyS7UWd6z7Dz2bgwMqaehPf-a6TFPpB459i5lam46JdKNH0r0Z8SVjNEcTNPem5pV2k4ODg3cV9oU0RwWXFHdUlpbC0ydUZLRXdyRFJwMDZCMW5nNDZBRG5LZTJ1QzFLcXAyV29KTTNaelUxMHFkLU1KVFFramZkalFxMnpBIIEC; bili_jct=019f8b4045241197796aace28d79a311; sid=575k0iix; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bp_t_offset_16107971=1175944487818493952; CURRENT_FNVAL=4048; b_lsid=6DF899DC_19CB99459D0"
    
    crawler = BVBilibiliCrawlerV4(cookie=cookie)
    videos = crawler.get_all_bvids(mid='28346875', max_pages=50)
    
    if videos:
        crawler.save_bvids(videos)
        
        print("\n" + "="*60)
        print("BV号列表:")
        print("="*60)
        print("target_bvids = [")
        for v in videos[:20]:
            print(f"    \"{v['bvid']}\",  # {v.get('title', '')[:30]}...")
        if len(videos) > 20:
            print(f"    # ... 还有 {len(videos)-20} 个视频")
        print("]")


if __name__ == "__main__":
    main()
