# -*- coding: utf-8 -*-
"""从meta.json补回feedback.json缺失的league"""
import json, os, re

FB = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Build league map from ALL meta.json files
league_map = {}

for date_dir in sorted(os.listdir(TASKS_DIR)):
    if not re.match(r'\d{4}-\d{2}-\d{2}', date_dir):
        continue
    task_path = os.path.join(TASKS_DIR, date_dir)
    if not os.path.isdir(task_path):
        continue
    
    # 1. Check root .md files (final reports)
    for fname in os.listdir(task_path):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(task_path, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            # Find match number from filename: 周日001_xxx.md
            mn = re.search(r'(周[一二三四五六日])(\d+)', fname)
            if not mn:
                continue
            match_num = mn.group(1) + mn.group(2).zfill(3)
            
            # Find league from meta.json in the same task dir
            meta_path = os.path.join(task_path, 'data', 'matches_data.json')
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        matches_data = json.load(mf)
                    for m in matches_data:
                        mn_field = m.get('match_num', '') or m.get('match_no', '')
                        if mn_field and mn_field == match_num:
                            league = m.get('league', '')
                            if league:
                                key = f'{date_dir}_{match_num}'
                                league_map[key] = league
                                break
                except:
                    pass
        except:
            continue
    
    # 2. Check data/match*/meta.json
    data_path = os.path.join(task_path, 'data')
    if os.path.isdir(data_path):
        for subdir in os.listdir(data_path):
            if not re.match(r'match\d+', subdir):
                continue
            meta_path = os.path.join(data_path, subdir, 'meta.json')
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    mi = meta.get('match_info', {})
                    week = mi.get('week', '')  # e.g., "周日"
                    match_no = mi.get('match_no', '')  # e.g., "1" or "001"
                    league = mi.get('league', '')
                    
                    if week and league:
                        # Normalize match_no
                        if match_no.isdigit():
                            match_no = match_no.zfill(3)
                        key = f'{date_dir}_{week}{match_no}'
                        league_map[key] = league
                except:
                    continue

print('Built league_map: %d entries' % len(league_map))

# Now fix feedback.json
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)

dates = data.get('dates', {})
fixed = 0

for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        if item.get('league', '') and item.get('league', '') != '未知':
            continue
        
        match_num = item.get('match_num', '')
        if not match_num:
            continue
        
        key = f'{date}_{match_num}'
        if key in league_map:
            item['league'] = league_map[key]
            fixed += 1
        else:
            # Try normalize
            m = re.match(r'(周[一二三四五六日])(\d+)$', match_num)
            if m:
                normalized = m.group(1) + m.group(2).zfill(3)
                key2 = f'{date}_{normalized}'
                if key2 in league_map:
                    item['league'] = league_map[key2]
                    fixed += 1
                    continue
            
            # Try without zfill
            m = re.match(r'(周[一二三四五六日])(\d+)$', match_num)
            if m:
                for zlen in [1, 2, 3]:
                    test_no = m.group(2).zfill(zlen)
                    test_key = f'{date}_{m.group(1)}{test_no}'
                    if test_key in league_map:
                        item['league'] = league_map[test_key]
                        fixed += 1
                        break

# Save
with open(FB, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Fixed: %d' % fixed)

# Verify
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)
dates = data.get('dates', {})
league_counts = {}
total = 0
for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        total += 1
        league = item.get('league', '未知')
        league_counts[league] = league_counts.get(league, 0) + 1

print('Total: %d' % total)
print('Unknown: %d' % league_counts.get('未知', 0))
for league, count in sorted(league_counts.items(), key=lambda x: -x[1])[:15]:
    print('  %s: %d' % (league, count))
