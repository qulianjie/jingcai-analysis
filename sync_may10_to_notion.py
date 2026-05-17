#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从5月10日竞彩任务目录读取比赛，同步到Notion数据库"""

import json
import requests
import re
import os
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'
DATE = '2026-05-10'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

# 读取竞彩任务目录
task_dir = f'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/{DATE}/data'
if not os.path.exists(task_dir):
    print(f'❌ 目录不存在: {task_dir}')
    sys.exit(1)

# 获取所有match目录
match_dirs = [d for d in os.listdir(task_dir) if os.path.isdir(os.path.join(task_dir, d)) and d.startswith('match')]
print(f'找到 {len(match_dirs)} 个match目录')

# 从final_report.md读取比赛信息
matches = []
for md_dir in sorted(match_dirs):
    report_file = os.path.join(task_dir, md_dir, 'final_report.md')
    if not os.path.exists(report_file):
        continue
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取比赛信息
    m = re.search(r'比赛名称：(.+)', content)
    if not m: continue
    
    match_name = m.group(1).strip()
    
    # 提取竞彩预测
    pred = ''
    pred_m = re.search(r'竞彩预测[：:](.+)', content)
    if pred_m:
        pred = pred_m.group(1).strip().split('\n')[0].strip()
    
    # 提取步26_庄家最看好
    step26 = ''
    s26_m = re.search(r'步26_庄家最看好[：:](.+)', content)
    if s26_m:
        step26 = s26_m.group(1).strip().split('\n')[0].strip()
    
    # 提取竞彩编号
    match_num = ''
    num_m = re.search(r'竞彩编号[：:](.+)', content)
    if num_m:
        match_num = num_m.group(1).strip().split('\n')[0].strip()
    
    matches.append({
        'match_num': match_num,
        'match_name': match_name,
        'pred': pred,
        'step26': step26,
    })

print(f'提取到 {len(matches)} 场比赛信息')

# 查询Notion中已存在的5月10日比赛
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {
        'and': [
            {'property': '比赛日期', 'date': {'equals': DATE}},
        ]
    },
    'page_size': 100
}))
existing = r.json()['results']
existing_names = set()
for p in existing:
    name = p['properties']['Name']['title'][0]['plain_text']
    existing_names.add(name)

print(f'Notion中已有 {len(existing)} 场5月10日比赛')

# 同步新比赛
created = 0
for match in matches:
    if match['match_name'] in existing_names:
        continue
    
    props = {
        'Name': {'title': [{'text': {'content': match['match_name']}}]},
        '比赛日期': {'date': {'start': DATE}},
        '竞彩编号': {'rich_text': [{'text': {'content': match['match_num']}}]},
        '竞彩预测': {'rich_text': [{'text': {'content': match['pred']}}]},
        '步26_庄家最看好': {'rich_text': [{'text': {'content': match['step26']}}]},
    }
    
    data = json.dumps({'parent': {'database_id': DB_ID}, 'properties': props})
    r = requests.post('https://api.notion.com/v1/pages', headers=HEADERS, data=data)
    
    if r.status_code == 200:
        print(f'  ✅ 创建: {match["match_name"]}')
        created += 1
    else:
        print(f'  ❌ 失败: {match["match_name"]} - {r.status_code}')

print(f'\n创建 {created} 场新比赛')

# 验证
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛日期', 'date': {'equals': DATE}},
    'page_size': 100
}))
final = r.json()['results']
print(f'验证: Notion中5月10日比赛共 {len(final)} 场')
