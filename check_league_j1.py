# -*- coding: utf-8 -*-
import json, os

SCRIPT_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai'
json_path = os.path.join(SCRIPT_DIR, 'leagues_all.json')

with open(json_path, 'r', encoding='utf-8') as f:
    leagues = json.load(f)

# Find 日职 related
print('Searching for 日职/J1/J-League:')
for item in leagues:
    name = item['name']
    if 'J1' in name or 'J2' in name or 'J3' in name or 'League' in name or '日' in name:
        print(f'  id={item["id"]} name={repr(name)}')

print('\n\nAll leagues with id 19xxx:')
for item in leagues:
    if item['id'].startswith('19'):
        print(f'  id={item["id"]} name={repr(item["name"])}')
