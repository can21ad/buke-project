import json

with open('../packages/web/public/data/buke_all_episodes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = data['videos']

special_keywords = ['特辑', '100期', '200期', '300期', '春节', '中秋', '端午', '元旦', '国庆', '情人节', '万圣节', '圣诞节', '元宵', '清明', '劳动节', '儿童节', '教师节', '重阳', '除夕', '过年', '新年']

print('=== 特辑分类检查 ===')
print()

special_videos = []
for v in videos:
    title = v['title']
    if '道听途说' in title:
        for kw in special_keywords:
            if kw in title:
                special_videos.append({
                    'title': title[:50],
                    'keyword': kw,
                    'episode': v.get('episode', 0)
                })
                break

print(f'找到 {len(special_videos)} 个特辑视频:')
print()
for v in special_videos[:20]:
    print(f'  [{v["keyword"]}] 第{v["episode"]}期: {v["title"]}...')

if len(special_videos) > 20:
    print(f'  ... 还有 {len(special_videos) - 20} 个')

print()
print('=== 只搜索"特辑"关键词 ===')
teji_videos = [v for v in videos if '特辑' in v['title']]
print(f'找到 {len(teji_videos)} 个包含"特辑"的视频:')
for v in teji_videos[:20]:
    print(f'  第{v.get("episode", 0)}期: {v["title"][:50]}...')
