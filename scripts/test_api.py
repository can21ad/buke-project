import requests
import json

# 测试多个BV号
bvids = ['BV1W8h9znETX', 'BV1dAgGzNEQq', 'BV1aK411A7of']

for bvid in bvids:
    r = requests.get(f'http://localhost:8000/api/similar?bvid={bvid}&top_n=2')
    data = r.json()
    print(f'\n=== {bvid} 的相似视频 ===')
    if data.get('code') == 200:
        for v in data['data']['videos']:
            print(f'  {v["rank"]}. {v["title"][:30]}... 相似度: {v["similarity"]}')
