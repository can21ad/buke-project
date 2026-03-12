import requests

r = requests.get('http://localhost:8000/api/search?keyword=灵异&top_n=1')
d = r.json()
if d.get('data') and d['data']['videos']:
    v = d['data']['videos'][0]
    print('返回结果:')
    print('  title:', v.get('title', '')[:30])
    print('  views:', v.get('views'))
    print('  play_count:', v.get('play_count'))
    print('  comment_count:', v.get('comment_count'))
    print('  duration_str:', v.get('duration_str'))
    print('  cover_local:', v.get('cover_local'))
    print('  upload_date:', v.get('upload_date'))
