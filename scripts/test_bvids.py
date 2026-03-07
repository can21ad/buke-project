import requests
import json

# 测试BV号是否有效
bvids_to_test = [
    "BV1Gg6iB9EbS",
    "BV1D1qpB6ECc", 
    "BV19SiFB1E1q",
    # 从搜索结果获取更多BV号
    "BV1vh3gzwE4H",
    "BV1MLTxz9EZE",
    "BV1xx411c7mD",
    "BV1D1641k7mD",
    "BV1xx411c7mE",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com/'
}

print("测试BV号有效性...\n")

valid_bvids = []

for bvid in bvids_to_test:
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data['code'] == 0:
            title = data['data']['title']
            print(f"✅ {bvid}: {title[:40]}...")
            valid_bvids.append(bvid)
        else:
            print(f"❌ {bvid}: 无效或不存在")
    except Exception as e:
        print(f"❌ {bvid}: 请求失败 - {e}")

print(f"\n有效BV号数量: {len(valid_bvids)}")
print("\n建议使用以下有效BV号更新爬虫配置:")
print(json.dumps(valid_bvids, ensure_ascii=False, indent=2))