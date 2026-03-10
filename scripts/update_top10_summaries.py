import csv
import json
from datetime import datetime

# 读取 top10_help_comments.json 文件，获取前10个视频的BV号
top10_file_path = 'D:\\怖客\\packages\\web\\public\\data\\top10_help_comments.json'
with open(top10_file_path, 'r', encoding='utf-8') as f:
    top10_data = json.load(f)

top10_bvids = []
top10_videos = []

# 提取前10个视频的信息
for video in top10_data['videos'][:10]:
    bvid = video['bvid']
    top10_bvids.append(bvid)
    top10_videos.append({
        'rank': video['rank'],
        'bvid': bvid,
        'title': video['title'],
        'play_count': video['play_count'],
        'cover_url': video['cover_url'],
        'cover_local': video['cover_local'],
        'comment_count': video['comment_count'],
        'comments': video['comments']
    })

print(f"获取到前10个视频的BV号: {top10_bvids}")

# 读取 space_merged_with_summary.csv 文件，找到对应的BV号的总结内容
csv_file_path = 'D:\\怖客\\scripts\\space_merged_with_summary.csv'
bv_summary_map = {}

# 尝试不同的编码
encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
success = False

for encoding in encodings:
    try:
        with open(csv_file_path, 'r', encoding=encoding) as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                if row.get('bvid'):
                    bvid = row['bvid']
                    summary = row.get('summary', '')
                    bv_summary_map[bvid] = summary
        success = True
        print(f"使用 {encoding} 编码成功读取CSV文件")
        break
    except Exception as e:
        print(f"尝试 {encoding} 编码失败: {e}")
        continue

if not success:
    print("所有编码尝试都失败了，无法读取CSV文件")
    exit(1)

print(f"从CSV文件中读取了 {len(bv_summary_map)} 条记录")

# 更新前10个视频的总结内容
for video in top10_videos:
    bvid = video['bvid']
    if bvid in bv_summary_map:
        video['summary'] = bv_summary_map[bvid]
        print(f"更新了视频 {bvid} 的总结")
    else:
        print(f"警告: 未找到视频 {bvid} 的总结")

# 构建新的JSON数据
new_top10_data = {
    "generated_at": datetime.now().isoformat(),
    "total_videos": len(top10_videos),
    "total_comments": sum(video['comment_count'] for video in top10_videos),
    "keywords": top10_data['keywords'],
    "videos": top10_videos
}

# 写入新的JSON文件
output_file_path = 'D:\\怖客\\packages\\web\\public\\data\\top10_help_comments_updated.json'
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(new_top10_data, f, ensure_ascii=False, indent=2)

print(f"更新完成！文件已保存到: {output_file_path}")
