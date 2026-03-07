import json
from datetime import datetime

# 读取爬虫结果
with open('buke_crawler_v3_merged.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 转换为前端格式
stories = []
story_id = 0

for result in data['results']:
    source_video = result['source_video']
    source_bvid = result['source_bvid']
    
    for story in result['past_stories']:
        story_id += 1
        
        # 提取时间标记中的第一个作为主要时间点
        time_markers = story.get('time_markers', [])
        timestamp = 0
        if time_markers:
            # 解析时间格式 "12:34" 或 "1:23:45"
            first_marker = time_markers[0]
            parts = first_marker.split(':')
            if len(parts) == 2:
                timestamp = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                timestamp = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        
        # 获取评论内容作为故事描述
        comments = story.get('comments', [])
        review = comments[0]['content'] if comments else story['name']
        
        # 提取标签
        tags = story.get('bv_list', [])[:3]
        if not tags:
            tags = ['道听途说', '热门故事']
        
        stories.append({
            'id': story_id,
            'name': story['name'],
            'title': source_video[:50] + '...' if len(source_video) > 50 else source_video,
            'bvid': source_bvid,
            'timestamp': timestamp,
            'heat': story['heat_score'],
            'mention_count': story['mention_count'],
            'review': review[:500] if len(review) > 500 else review,
            'length': len(review),
            'author': '@大佬何金银',
            'tags': tags[:4],
            'time_markers': time_markers[:5],
            'related_bvs': story.get('bv_list', []),
            'jump_url': f"https://www.bilibili.com/video/{source_bvid}?t={timestamp}&p=1"
        })

# 按热度排序
stories.sort(key=lambda x: x['heat'], reverse=True)

# 取Top 50
top_stories = stories[:50]

# 生成输出
output = {
    'generated_at': datetime.now().isoformat(),
    'version': 'v3.0',
    'total_stories': len(stories),
    'top_n': len(top_stories),
    'theme': '【道听途说系列】热门故事精选',
    'keywords': ['道听途说', '灵异', '恐怖', '真实经历', '民间传说'],
    'stories': top_stories
}

# 保存
with open('../packages/web/public/data/buke_top_stories.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"[+] 转换完成，共 {len(top_stories)} 条故事")
print(f"[+] 数据已保存至: packages/web/public/data/buke_top_stories.json")