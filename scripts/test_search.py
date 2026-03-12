import requests

# 测试过滤搜索
print("=== 搜索'民间怪谈' + 10分钟内 ===")
r = requests.get('http://localhost:8000/api/search?keyword=民间怪谈&max_duration=10&top_n=5')
d = r.json()
if d.get('data') and d['data']['videos']:
    for v in d['data']['videos']:
        print(f"  {v['title'][:35]} 时长:{v['duration']}")
else:
    print("  未找到")

print("\n=== 搜索'校园灵异' + 评论1000+ ===")
r = requests.get('http://localhost:8000/api/search?keyword=校园灵异&min_comments=1000&top_n=5')
d = r.json()
if d.get('data') and d['data']['videos']:
    for v in d['data']['videos']:
        print(f"  {v['title'][:35]} 评论:{v['comment_count']}")
else:
    print("  未找到")

print("\n=== 搜索'医院灵异' + 最新 ===")
r = requests.get('http://localhost:8000/api/search?keyword=医院灵异&sort_by=date&top_n=3')
d = r.json()
if d.get('data') and d['data']['videos']:
    for v in d['data']['videos']:
        print(f"  {v['title'][:35]} 日期:{v['upload_date']}")
else:
    print("  未找到")
