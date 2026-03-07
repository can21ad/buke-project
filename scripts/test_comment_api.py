import requests
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

def get_comments_v1(aid, page=1):
    url = "https://api.bilibili.com/x/v2/reply"
    params = {
        "type": 1,
        "oid": aid,
        "pn": page,
        "ps": 20,
        "sort": 2,
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
        print(f"v2/reply 响应: code={data.get('code')}, message={data.get('message')}")
        if data.get('code') == 0:
            replies = data['data'].get('replies', [])
            print(f"  获取到 {len(replies)} 条评论")
            for r in replies[:3]:
                print(f"    - {r['content']['message'][:50]}...")
            return replies
    except Exception as e:
        print(f"异常: {e}")
    return []

aid = 113719744926459
print(f"测试视频 AID: {aid}")
print()

print("=== 测试 v2/reply API ===")
get_comments_v1(aid)

print("\n=== 测试 v2/reply/main API ===")
url = "https://api.bilibili.com/x/v2/reply/main"
params = {
    "type": 1,
    "oid": aid,
    "next": 1,
    "mode": 3,
}
try:
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    data = resp.json()
    print(f"v2/reply/main 响应: code={data.get('code')}, message={data.get('message')}")
    if data.get('code') == 0:
        replies = data['data'].get('replies', [])
        print(f"  获取到 {len(replies)} 条评论")
except Exception as e:
    print(f"异常: {e}")

print("\n=== 测试 v2/reply/reply API (获取楼中楼) ===")
url = "https://api.bilibili.com/x/v2/reply/reply"
params = {
    "type": 1,
    "oid": aid,
    "root": 1,
    "pn": 1,
    "ps": 20,
}
try:
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    data = resp.json()
    print(f"v2/reply/reply 响应: code={data.get('code')}, message={data.get('message')}")
except Exception as e:
    print(f"异常: {e}")
