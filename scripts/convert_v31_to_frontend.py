import json
import os
from datetime import datetime

def load_ai_summaries():
    """加载AI总结数据"""
    summaries = {}
    script_dir = os.path.dirname(__file__)
    summary_file = os.path.join(script_dir, '..', 'ai_summaries.json')
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for s in data.get('summaries', []):
                summaries[s['bvid']] = s.get('ai_summary', {})
        print(f"[+] 加载了 {len(summaries)} 个AI总结")
    else:
        print(f"[!] AI总结文件不存在: {summary_file}")
    return summaries

def convert_to_frontend():
    """转换爬虫数据为前端格式"""
    
    script_dir = os.path.dirname(__file__)
    crawler_file = os.path.join(script_dir, 'buke_crawler_v31_merged.json')
    if not os.path.exists(crawler_file):
        print(f"[-] 找不到爬虫数据文件: {crawler_file}")
        return
    
    with open(crawler_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ai_summaries = load_ai_summaries()
    
    stories = []
    story_id = 0
    
    for result in data['results']:
        source_video = result['source_video']
        source_bvid = result['source_bvid']
        
        for story in result['past_stories']:
            story_id += 1
            
            time_markers = story.get('time_markers', [])
            timestamp = 0
            if time_markers:
                first_marker = time_markers[0]
                parts = first_marker.split(':')
                if len(parts) == 2:
                    try:
                        timestamp = int(parts[0]) * 60 + int(parts[1])
                    except:
                        pass
                elif len(parts) == 3:
                    try:
                        timestamp = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    except:
                        pass
            
            comments = story.get('comments', [])
            review = comments[0]['content'] if comments else story['name']
            
            tags = []
            if story.get('bv_list'):
                tags.extend(story['bv_list'][:2])
            if not tags:
                tags = ['道听途说', '热门故事']
            
            story_data = {
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
            }
            
            if source_bvid in ai_summaries:
                story_data['ai_summary'] = ai_summaries[source_bvid]
            
            stories.append(story_data)
    
    stories.sort(key=lambda x: x['heat'], reverse=True)
    
    top_stories = stories[:50]
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'version': 'v3.1',
        'total_stories': len(stories),
        'top_n': len(top_stories),
        'theme': '【道听途说系列】热门故事精选',
        'keywords': ['道听途说', '灵异', '恐怖', '真实经历', '民间传说'],
        'stories': top_stories
    }
    
    output_path = os.path.join(script_dir, '..', 'packages', 'web', 'public', 'data', 'buke_top_stories.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"[+] 转换完成，共 {len(top_stories)} 条故事")
    print(f"[+] 数据已保存至: {output_path}")
    
    ai_count = sum(1 for s in top_stories if 'ai_summary' in s)
    print(f"[+] 其中 {ai_count} 条故事有AI总结")
    
    print("\n热度TOP5:")
    for i, s in enumerate(top_stories[:5], 1):
        ai_tag = " [AI总结]" if 'ai_summary' in s else ""
        print(f"  {i}. {s['name']} - 热度: {s['heat']}{ai_tag}")

if __name__ == "__main__":
    convert_to_frontend()
