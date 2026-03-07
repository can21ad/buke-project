import json
with open('../packages/web/public/data/buke_all_episodes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = data['videos']

print('优化后的关键词示例:')
print('=' * 60)

for v in videos[:20]:
    kws = v.get('keywords', [])
    kw_str = ', '.join([k['word'] for k in kws])
    print(f'{v["title"][:35]}...')
    print(f'  关键词: {kw_str}')
    print()

from collections import Counter
keyword_counter = Counter()
for v in videos:
    for kw in v.get('keywords', []):
        keyword_counter[kw['word']] += 1

print('=' * 60)
print('关键词频率 TOP 30:')
for word, count in keyword_counter.most_common(30):
    print(f'  {word}: {count}')
