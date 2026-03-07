import json
with open('../packages/web/public/data/buke_all_episodes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = data['videos']
with_kw = [v for v in videos if v.get('keywords')]

print(f'有关键词的视频数量: {len(with_kw)}')
print()
for v in with_kw[:15]:
    kws = v.get('keywords', [])
    kw_str = ', '.join([k['word'] for k in kws])
    print(f'{v["title"][:40]}...')
    print(f'  关键词: {kw_str}')
    print()
