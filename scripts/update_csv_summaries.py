import csv
import json
from datetime import datetime

# 读取 CSV 文件
csv_file_path = 'D:\\怖客\\scripts\\space_merged_with_summary.csv'
summaries = []

# 尝试不同的编码
encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
success = False

for encoding in encodings:
    try:
        with open(csv_file_path, 'r', encoding=encoding) as csvfile:
            csv_reader = csv.DictReader(csvfile)
            rank = 1
            for row in csv_reader:
                # 跳过空行
                if not row.get('bvid'):
                    continue
                
                # 提取数据
                bvid = row['bvid']
                title = row.get('title', '')
                summary = row.get('summary', '')
                
                # 构建摘要对象
                summary_obj = {
                    "rank": rank,
                    "bvid": bvid,
                    "title": title,
                    "owner": "大佬何金银",  # 固定值
                    "duration": 0,  # CSV 中没有，设为默认值
                    "view_count": 0,  # CSV 中没有，设为默认值
                    "summary": summary,
                    "generated_at": datetime.now().isoformat()
                }
                
                summaries.append(summary_obj)
                rank += 1
        success = True
        print(f"使用 {encoding} 编码成功读取文件")
        break
    except Exception as e:
        print(f"尝试 {encoding} 编码失败: {e}")
        continue

if not success:
    print("所有编码尝试都失败了，无法读取CSV文件")
    exit(1)

# 构建 JSON 数据
json_data = {
    "generated_at": datetime.now().isoformat(),
    "total": len(summaries),
    "summaries": summaries
}

# 写入 JSON 文件
json_file_path = 'D:\\怖客\\packages\\web\\public\\data\\csv_top10_summaries.json'
with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
    json.dump(json_data, jsonfile, ensure_ascii=False, indent=2)

print(f"更新完成！共处理 {len(summaries)} 条记录")
print(f"文件已保存到: {json_file_path}")
