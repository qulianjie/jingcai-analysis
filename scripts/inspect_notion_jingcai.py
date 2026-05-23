#!/usr/bin/env python3
import urllib.request, json, os

with open(os.path.expanduser('~/.config/notion/api_key'), 'rb') as f:
    raw = f.read()
    if raw.startswith(b'\xff\xfe'):
        raw = raw[2:]
    elif raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    key = raw.decode('utf-16-le' if b'\x00' in raw[:4] else 'utf-8').strip()

def notion(method, path, data=None):
    url = 'https://api.notion.com' + path
    headers = {
        'Authorization': 'Bearer ' + key,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json'
    }
    body = json.dumps(data, ensure_ascii=False).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# Property name mapping (hex -> Chinese)
PROP_NAMES = {
    'e4b8bbe9989fe4b8bbe59cba': '主队主场',
    'e58f8de9a688e680bbe7bb93': '反馈总结',
    'e58f8de9a688e697a5e69c9f': '反馈日期',
    'e5a487e6b3a8': '备注',
    'e5ae9ee99985e6af94e58886': '实际比分',
    'e5ae9ee99985e7bb93e69e9c': '实际结果',
    'e5aea2e9989fe5aea2e59cba': '客队客场',
    'e6aca7e8b594e8b68be58abf': '欧赔趋势',
    'e6ada532355fe5ba84e5aeb6e79b88e4ba8f': '第25_庄家盈利',
    'e6ada532365fe5ba84e5aeb6e69c80e79c8be5a5bd': '第26_庄家最看好',
    'e6ada532365fe5ba84e5aeb6e79b88e4ba8fe696b9e59091': '第26_庄家盈利方向',
    'e6ada532365fe68a95e6b3a8e58da0e6af94': '第26_投注占比',
    'e6ada532365fe79b88e4ba8fe58da0e6af94': '第26_盈利占比',
    'e6af94e8b59b': '比赛',
    'e6af94e8b59be697a5e69c9f': '比赛日期',
    'e6beb3e997a8e4ba9ae79b98': '澳门亚盘',
    'e799bee5aeb6e5afb9e6af94': '百家对比',
    'e799bee5aeb6e6aca7e8b594e5b9b3': '百家欧赔平',
    'e799bee5aeb6e6aca7e8b594e8839c': '百家欧赔胜',
    'e799bee5aeb6e6aca7e8b594e8b49f': '百家欧赔负',
    'e7ab9ee5bda9e6aca7e8b594e5b9b3': '竞彩欧赔平',
    'e7ab9ee5bda9e6aca7e8b594e8839c': '竞彩欧赔胜',
    'e7ab9ee5bda9e6aca7e8b594e8b49f': '竞彩欧赔负',
    'e7ab9ee5bda9e6beb3e997a8e4ba9ae79b98': '竞彩澳门亚盘',
    'e7ab9ee5bda9e9a284e6b58b': '竞彩预测',
    'e7bb88e79b98496e74657277657474656ee5b9b3': '终盘Interwetten平',
    'e7bb88e79b98496e74657277657474656ee8839c': '终盘Interwetten胜',
    'e7bb88e79b98496e74657277657474656ee8b49f': '终盘Interwetten负',
    'e7bb88e79b98e799bee5aeb6e6aca7e8b594e5b9b3': '终盘百家欧赔平',
    'e7bb88e79b98e799bee5aeb6e6aca7e8b594e8839c': '终盘百家欧赔胜',
    'e7bb88e79b98e799bee5aeb6e6aca7e8b594e8b49f': '终盘百家欧赔负',
    'e7bb88e79b98e7ab9ee5bda9e6aca7e8b594e5b9b3': '终盘竞彩欧赔平',
    'e7bb88e79b98e7ab9ee5bda9e6aca7e8b594e8839c': '终盘竞彩欧赔胜',
    'e7bb88e79b98e7ab9ee5bda9e6aca7e8b594e8b49f': '终盘竞彩欧赔负',
    'e7bb88e79b98e7ab9ee5bda9e6beb3e997a8e4ba9ae79b98': '终盘竞彩澳门亚盘',
    'e7bb88e79b98e8aea9e79083e68c87e695b0e5b9b3': '终盘让球指数平',
    'e7bb88e79b98e8aea9e79083e68c87e695b0e8839c': '终盘让球指数胜',
    'e7bb88e79b98e8aea9e79083e68c87e695b0e8b49f': '终盘让球指数负',
    'e8aea9e79083e68c87e695b0e5b9b3': '让球指数平',
    'e8aea9e79083e68c87e695b0e8839c': '让球指数胜',
    'e8aea9e79083e68c87e695b0e8b49f': '让球指数负',
    'e8aea9e79083e9a284e6b58b': '让球预测',
    'e8aea9e79083e9a284e6b58be6ada3e7a1ae': '让球预测正确',
    'e9a284e6b58be6ada3e7a1ae': '预测正确',
    'e9a38ee999a9e68f90e7a4ba': '风险提示',
    '4957e5908ce8b594': 'IW同赔',
    '496e74657277657474656ee5b9b3': 'Interwetten平',
    '496e74657277657474656ee8839c': 'Interwetten胜',
    '496e74657277657474656ee8b49f': 'Interwetten负',
}

def get_cn(k):
    h = k.encode('utf-8').hex()
    return PROP_NAMES.get(h, k)

def get_prop(props, target_name):
    for k, v in props.items():
        if get_cn(k) == target_name:
            return v
    return None

# Get pages
r = notion('POST', '/v1/search', {'page_size': 100})
all_pages = list(r['results'])
cursor = r.get('next_cursor')
page_count = 0
while cursor and page_count < 4:
    r2 = notion('POST', '/v1/search', {'page_size': 100, 'start_cursor': cursor})
    all_pages.extend(r2['results'])
    cursor = r2.get('next_cursor')
    page_count += 1

dbpages = [p for p in all_pages if p.get('parent', {}).get('database_id') == '35491ad7-17ba-81cc-aa04-ce53f7234e17']
print(f'Total pages: {len(dbpages)}')

# Show a few samples with the 4 key fields
key_fields = ['竞彩预测', '第26_庄家最看好', '让球预测', '竞彩欧赔胜', '比赛', '比赛日期', '反馈总结']
for p in dbpages[:10]:
    props = p['properties']
    title = props['Name']['title'][0]['plain_text']
    print(f'\n=== {title} ===')
    for f in key_fields:
        v = get_prop(props, f)
        if v is None:
            continue
        if v['type'] == 'rich_text' and v.get('rich_text'):
            txt = v['rich_text'][0]['plain_text'][:80]
            print(f'  {f}: {txt}')
        elif v['type'] == 'number' and v.get('number') is not None:
            print(f'  {f}: {v["number"]}')
    print()
