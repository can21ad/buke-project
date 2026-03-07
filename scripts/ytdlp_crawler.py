#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怖客 (Buke) - yt-dlp 视频爬虫 V3
==========================================
使用 yt-dlp 爬取B站UP主投稿页面的所有BV号
GitHub: https://github.com/yt-dlp/yt-dlp
"""

import yt_dlp
import json
import os
import re
import time
from typing import List, Dict, Optional
from datetime import datetime


class YtdlpBilibiliCrawler:
    """基于 yt-dlp 的B站视频爬虫"""
    
    def __init__(self, cookie: str = ''):
        self.cookie = cookie
        self.cookie_file = None
        
        if cookie:
            self.cookie_file = self._create_cookie_file(cookie)
        
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
            },
        }
        
        if self.cookie_file:
            self.ydl_opts['cookiefile'] = self.cookie_file
    
    def _create_cookie_file(self, cookie: str) -> str:
        """创建Netscape格式的cookie文件"""
        cookie_file = 'bilibili_cookies.txt'
        
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
            f.write("# This is a generated file!  Do not edit.\n\n")
            
            for item in cookie.split('; '):
                if '=' in item:
                    name, value = item.split('=', 1)
                    f.write(f".bilibili.com\tTRUE\t/\tFALSE\t0\t{name}\t{value}\n")
        
        return cookie_file
    
    def get_all_bvids(self, mid: str, max_videos: int = 500) -> List[Dict]:
        """获取UP主投稿页面的所有BV号"""
        url = f"https://space.bilibili.com/{mid}/upload/video"
        
        opts = {
            **self.ydl_opts,
            'playlistend': max_videos,
            'extract_flat': 'in_playlist',
        }
        
        videos = []
        print(f"[*] 正在获取UP主 {mid} 投稿页面的所有视频...")
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    print(f"[+] 播放列表: {info.get('title', 'N/A')}")
                    print(f"[+] 视频总数: {info.get('playlist_count', 'N/A')}")
                    
                    if 'entries' in info:
                        for i, entry in enumerate(info['entries'], 1):
                            if entry:
                                videos.append({
                                    'index': i,
                                    'bvid': entry.get('id', ''),
                                    'title': entry.get('title', ''),
                                    'duration': entry.get('duration', 0),
                                    'view_count': entry.get('view_count', 0),
                                    'url': f"https://www.bilibili.com/video/{entry.get('id', '')}",
                                })
                                
                                if i % 20 == 0:
                                    print(f"  已获取 {i} 个视频...")
                        
                        print(f"\n[+] 共获取到 {len(videos)} 个视频")
        
        except Exception as e:
            print(f"[-] 获取视频失败: {e}")
        
        return videos
    
    def save_bvids(self, videos: List[Dict], output_file: str = 'all_bvids.json') -> Dict:
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
    
    def print_bvid_list(self, videos: List[Dict]):
        """打印BV号列表（可直接复制使用）"""
        print("\n" + "="*60)
        print("BV号列表 (可直接复制到爬虫配置):")
        print("="*60)
        
        print("\n# Python列表格式")
        print("target_bvids = [")
        for v in videos[:30]:
            print(f"    \"{v['bvid']}\",")
        if len(videos) > 30:
            print(f"    # ... 还有 {len(videos)-30} 个视频")
        print("]")
        
        print("\n# 纯BV号列表")
        for v in videos[:50]:
            print(v['bvid'])
        if len(videos) > 50:
            print(f"# ... 还有 {len(videos)-50} 个")
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """获取单个视频信息"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    return {
                        'bvid': info.get('id', ''),
                        'title': info.get('title', ''),
                        'description': info.get('description', ''),
                        'duration': info.get('duration', 0),
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0),
                        'comment_count': info.get('comment_count', 0),
                        'upload_date': info.get('upload_date', ''),
                        'uploader': info.get('uploader', ''),
                        'uploader_id': info.get('uploader_id', ''),
                        'thumbnail': info.get('thumbnail', ''),
                        'tags': info.get('tags', []),
                        'url': url,
                    }
        except Exception as e:
            print(f"[-] 获取视频信息失败: {e}")
        
        return None
    
    def batch_get_info(self, bvids: List[str], output_file: str = 'video_infos.json') -> List[Dict]:
        """批量获取视频信息"""
        results = []
        
        for i, bvid in enumerate(bvids, 1):
            print(f"\n[{i}/{len(bvids)}] 处理: {bvid}")
            
            url = f"https://www.bilibili.com/video/{bvid}"
            info = self.get_video_info(url)
            
            if info:
                results.append(info)
                print(f"  [+] {info['bvid']}: {info['title'][:40]}...")
            else:
                print(f"  [-] 获取失败")
            
            time.sleep(0.5)
        
        output = {
            'generated_at': datetime.now().isoformat(),
            'total_videos': len(results),
            'videos': results,
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n[+] 结果已保存至: {output_file}")
        return results


def main():
    """主函数"""
    print("="*60)
    print("怖客 - yt-dlp BV号爬虫")
    print("="*60)
    
    cookie = "buvid3=71D20EC7-CD73-A9EE-95BB-CE609A483B6289708infoc; b_nut=1767273489; _uuid=A99F32B5-67AC-107EC-3F68-D823D47E101C987664infoc; buvid4=9C7B018B-FA0C-531B-8C84-29BF798A4F6079733-024112904-2VYlXdb/AWHESum/Ib/uNw%3D%3D; buvid_fp=c5a6cd5b192d369df890a97db880fea8; rpdid=|(umY)~lY)ml0J'u~Y~k~Jl)|; DedeUserID=16107971; DedeUserID__ckMd5=95a6700915125197; theme-tip-show=SHOWED; hit-dyn-v2=1; __itrace_wid=fd682858-9fa6-4ccb-28b2-a82e62ee6170; LIVE_BUVID=AUTO3317672736233835; theme-avatar-tip-show=SHOWED; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1707-900; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3MDM3MDUsImlhdCI6MTc3MjQ0NDQ0NSwicGx0IjotMX0.jJ8uRdHhcV20bl1uTXzBZcP-obdgB7EFRArutjbbkXc; bili_ticket_expires=1772703645; SESSDATA=2472a2ba%2C1788001684%2C9597f%2A32CjCu75QuNog6ez4sRyS7UWd6z7Dz2bgwMqaehPf-a6TFPpB459i5lam46JdKNH0r0Z8SVjNEcTNPem5pV2k4ODg3cV9oU0RwWXFHdUlpbC0ydUZLRXdyRFJwMDZCMW5nNDZBRG5LZTJ1QzFLcXAyV29KTTNaelUxMHFkLU1KVFFramZkalFxMnpBIIEC; bili_jct=019f8b4045241197796aace28d79a311; sid=575k0iix; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bp_t_offset_16107971=1175944487818493952; CURRENT_FNVAL=4048; b_lsid=6DF899DC_19CB99459D0"
    
    crawler = YtdlpBilibiliCrawler(cookie=cookie)
    
    mid = '28346875'
    max_videos = 500
    
    videos = crawler.get_all_bvids(mid, max_videos)
    
    if videos:
        crawler.save_bvids(videos, 'all_bvids.json')
        crawler.print_bvid_list(videos)
        
        print(f"\n[+] 完成！共获取 {len(videos)} 个BV号")


if __name__ == "__main__":
    main()
