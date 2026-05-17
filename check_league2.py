# -*- coding: utf-8 -*-
import json, re

with open('C:/Users/lianjie/.openclaw/workspace/jingcai/leagues_all.json', 'r', encoding='utf-8') as f:
    leagues = json.load(f)

# Check what the names look like
print('Sample names:')
for item in leagues[:10]:
    name = item['name']
    # Extract Chinese prefix (before English letters)
    m = re.match(r'^([\u4e00-\u9fff]+)', name)
    cn = m.group(1) if m else 'NO_CHINESE'
    print(f'  id={item["id"]} full="{name}" cn_prefix="{cn}"')
