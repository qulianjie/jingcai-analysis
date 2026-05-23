#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request, json, os, re

with open(os.path.expanduser('~/.config/notion/api_key'), 'rb') as f:
    raw = f.read()
    if raw.startswith(b'\xff\xfe'): raw = raw[2:]
    elif raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
    key = raw.decode('utf-16-le' if b'\x00' in raw[:4] else 'utf-8').strip()

def n(m, p, d=None):
    url = 'https://api.notion.com' + p
    hd = {'Authorization': 'Bearer '+key, 'Notion-Version': '2025-09-03', 'Content-Type': 'application/json'}
    body = json.dumps(d, ensure_ascii=False).encode('utf-8') if d else None
    req = urllib.request.Request(url, data=body, headers=hd, method=m)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

DB_TRACK = '35491ad7-17ba-81cc-aa04-ce53f7234e17'  # 竞彩比赛追踪
DB_SUM = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9'     # 历史每日报告汇总

CN_MAP = {
    'e4b8bbe9989f': '主队', 'e5aea2e9989f': '客队', 'e6af94e8b59b': '比赛',
    'e6af94e8b59be697b6e997b4': '比赛时间', 'e88194e8b59b': '联赛',
    'e7ab9ee5bda9e9a284e6b58b': '竞彩预测', 'e7ab9ee5bda9e4bfa1e5bf83': '竞彩信心',
    'e6beb3e997a8e4ba9ae79b98': '澳门亚盘', 'e8aea9e79083': '让球',
    'e69c80e7bb88e7bb93e8aeba': '最终结论',
    'e7acac31e6ada5':'第1步','e7acac32e6ada5':'第2步','e7acac33e6ada5':'第3步',
    'e7acac34e6ada5':'第4步','e7acac35e6ada5':'第5步','e7acac36e6ada5':'第6步',
    'e7acac37e6ada5':'第7步','e7acac38e6ada5':'第8步','e7acac39e6ada5':'第9步',
    'e7acac3130e6ada5':'第10步','e7acac3131e6ada5':'第11步','e7acac3132e6ada5':'第12步',
    'e7acac3133e6ada5':'第13步','e7acac3134e6ada5':'第14步','e7acac3135e6ada5':'第15步',
    'e7acac3136e6ada5':'第16步','e7acac3137e6ada5':'第17步','e7acac3138e6ada5':'第18步',
    'e7acac3139e6ada5':'第19步','e7acac3230e6ada5':'第20步','e7acac3231e6ada5':'第21步',
    'e7acac3232e6ada5':'第22步','e7acac3233e6ada5':'第23步','e7acac3234e6ada5':'第24步',
    'e7acac3235e6ada5':'第25步','e7acac3236e6ada5':'第26步',
}

def cn_from_hex(h):
    return CN_MAP.get(h, bytes.fromhex(h).decode('utf-8', errors='replace'))

def extract_result(text):
    if not text: return None, None
    m = re.search(r'\|\s*(胜|平|负)\s*\((\d+:\d+)\)', text) or re.search(r'(胜|平|负)\s*\((\d+:\d+)\)', text)
    return (m.group(1), m.group(2)) if m else (None, None)

# 1. 拉追踪库数据
print('=== 读取竞彩追踪数据库 ===')
all_pages, cursor = [], None
for _ in range(6):
    params = {'page_size': 100}
    if cursor: params['start_cursor'] = cursor
    r = n('POST', '/v1/search', params)
    all_pages.extend(r['results'])
    cursor = r.get('next_cursor')
    if not r.get('has_more') or not cursor: break
db_track = [p for p in all_pages if p.get('parent',{}).get('database_id')==DB_TRACK]

track_data = {}
for p in db_track:
    props = p['properties']
    name = props.get('Name',{}).get('title',[''])[0].get('plain_text','') if props.get('Name',{}).get('title') else ''
    if not name: continue
    summary = ''
    for k, v in props.items():
        if cn_from_hex(k.encode('utf-8').hex()) == '反馈总结' and v['type']=='rich_text' and v.get('rich_text'):
            summary = v['rich_text'][0]['plain_text']
            break
    result, score = extract_result(summary)
    track_data[name] = {'result': result, 'score': score, 'summary': summary}

with_result = sum(1 for v in track_data.values() if v['result'])
print(f'追踪库: {len(track_data)} 条, 有赛果: {with_result}')

# 2. 拉汇总库
print('\n=== 读取历史每日报告汇总数据库 ===')
sum_pages = [p for p in all_pages if p.get('parent',{}).get('database_id')==DB_SUM]
# 也有可能在另一个请求里
if len(sum_pages) < 5:
    r2 = n('POST', '/v1/search', {'page_size': 100})
    for p in r2['results']:
        if p.get('parent',{}).get('database_id')==DB_SUM and p not in sum_pages:
            sum_pages.append(p)

print(f'汇总库: {len(sum_pages)} 条')

sum_names = set()
for p in sum_pages:
    props = p['properties']
    name = props.get('比赛',{}).get('title',[''])[0].get('plain_text','') if props.get('比赛',{}).get('title') else ''
    if not name:
        name = props.get('Name',{}).get('title',[''])[0].get('plain_text','') if props.get('Name',{}).get('title') else ''
    if name:
        sum_names.add(name)

# 3. 找出没在汇总库的
missing = {k:v for k,v in track_data.items() if k not in sum_names and v['result']}
print(f'\n=== 追踪库有赛果但汇总库缺少的: {len(missing)} 条 ===')

# 按日期排序
def get_date(name):
    m = re.match(r'(周一|周二|周三|周四|周五|周六|周日)(\d{3})', name)
    return m.group(0) if m else ''

sorted_missing = sorted(missing.items(), key=lambda x: x[1].get('summary',''))

for name, data in sorted_missing[:20]:
    print(f'  {name} | {data["result"]} ({data["score"]})')
if len(sorted_missing) > 20:
    print(f'  ...还有 {len(sorted_missing)-20} 条')

# 4. 输出汇总库已有的所有日期范围
print(f'\n=== 汇总库已有比赛 ({len(sum_names)} 条) ===')
for n in sorted(sum_names):
    print(f'  {n}')
