# -*- coding: utf-8 -*-
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Unknown dates
unknown_dates = [
    '2026-04-03', '2026-04-04', '2026-04-05', '2026-04-06', '2026-04-07',
    '2026-04-08', '2026-04-09', '2026-04-10', '2026-04-11', '2026-04-12',
    '2026-04-13', '2026-04-14', '2026-04-15', '2026-04-16', '2026-04-17',
    '2026-04-18', '2026-04-19', '2026-04-20', '2026-04-21', '2026-04-22',
    '2026-04-29',
]

# Build match_num -> teams from report files
match_teams = {}
for date in unknown_dates:
    date_dir = os.path.join(TASKS_DIR, date)
    if not os.path.isdir(date_dir):
        continue
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        m = re.match(r'(周[一二三四五六日]\d+)[_~](.+)\.md', os.path.basename(f))
        if m:
            match_num = m.group(1).strip()
            teams = m.group(2).strip()
            match_teams[match_num] = teams

# Build match_num -> teams from data/match*/meta.json
for date in unknown_dates:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    if not os.path.isdir(data_dir):
        continue
    for d in os.listdir(data_dir):
        if not d.startswith('match'):
            continue
        meta_file = os.path.join(data_dir, d, 'meta.json')
        if os.path.exists(meta_file):
            try:
                meta = json.load(open(meta_file, encoding='utf-8'))
                mn = meta.get('matchnum', '')
                teams = meta.get('home_team', '') + 'vs' + meta.get('away_team', '')
                if mn:
                    match_teams[mn] = teams
            except:
                pass

# Now build output
fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))

from datetime import datetime as dt
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

for date_str in unknown_dates:
    date_data = fb.get('dates', {}).get(date_str, {})
    if not date_data:
        continue
    
    items = []
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        if not league or league == '未知' or league.strip() == '':
            mn = item.get('match_num', '')
            # Normalize: add weekday prefix, 3-digit number
            try:
                dt_obj = dt.strptime(date_str, '%Y-%m-%d')
                wd = weekday_names[dt_obj.weekday()]
                # Extract number part
                if mn and not mn.startswith('周'):
                    num = mn
                    if num.isdigit():
                        num = num.zfill(3)
                    mn = wd + num
            except:
                pass
            
            teams = match_teams.get(mn, '???')
            items.append(f'  {mn}  {teams}  {item.get("score", "")}')
    
    if items:
        print(f'\n=== [{date_str}] {len(items)}场 ===')
        for it in items:
            print(it)
