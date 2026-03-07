import json
with open('../packages/web/public/data/buke_all_episodes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = data['videos']

without_kw = [v for v in videos if not v.get('keywords') or len(v.get('keywords', [])) == 0]
with_kw = [v for v in videos if v.get('keywords') and len(v.get('keywords', [])) > 0]

print(f'总视频数量: {len(videos)}')
print(f'有关键词: {len(with_kw)}')
print(f'无关键词: {len(without_kw)}')
print()
print('无关键词的视频:')
for v in without_kw[:20]:
    print(f'  {v["bvid"]}: {v["title"][:40]}...')
if len(without_kw) > 20:
    print(f'  ... 还有 {len(without_kw) - 20} 个')
