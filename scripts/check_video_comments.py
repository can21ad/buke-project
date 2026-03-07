import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/",
}

def check_video(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if data['code'] == 0:
            info = data['data']
            return {
                'title': info.get('title', ''),
                'view': info.get('stat', {}).get('view', 0),
                'reply': info.get('stat', {}).get('reply', 0),
                'aid': info.get('aid', 0),
            }
    except Exception as e:
        return None
    return None

bvids = [
    "BV15BC6YHEC1",
    "BV1RuqaY2Eym",
    "BV16CULYzEbb",
    "BV1SrSnYuEqy",
    "BV1ujyTYHEyy",
]

for bvid in bvids:
    info = check_video(bvid)
    if info:
        print(f"BV: {bvid}")
        print(f"  标题: {info['title'][:40]}...")
        print(f"  播放: {info['view']}, 评论数: {info['reply']}, AID: {info['aid']}")
    print()
