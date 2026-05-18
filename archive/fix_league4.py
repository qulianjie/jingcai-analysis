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
    
    # Check data/match*/meta.json
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
                    # New format: top-level fields
                    matchnum = meta.get('matchnum', '')  # e.g., "周日010"
                    league = meta.get('league', '')
                    
                    if matchnum and league:
                        key = f'{date_dir}_{matchnum}'
                        league_map[key] = league
                except:
                    continue
    
    # Also check root-level meta.json (for dates without data/ subdir)
    root_meta = os.path.join(task_path, 'meta.json')
    if os.path.exists(root_meta):
        try:
            with open(root_meta, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            matchnum = meta.get('matchnum', '')
            league = meta.get('league', '')
            if matchnum and league:
                key = f'{date_dir}_{matchnum}'
                league_map[key] = league
        except:
            continue

print('Built league_map: %d entries' % len(league_map))
print('Sample:')
for k, v in list(league_map.items())[:10]:
    print('  %s -> %s' % (k, v))

# Now fix feedback.json
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)

dates = data.get('dates', {})
fixed = 0

for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        current_league = item.get('league', '')
        if current_league and current_league != '未知':
            continue  # already has valid league
        
        match_num = item.get('match_num', '')
        if not match_num:
            continue
        
        key = f'{date}_{match_num}'
        if key in league_map:
            item['league'] = league_map[key]
            fixed += 1
        else:
            # Try normalize: 周日1 -> 周日010
            m = re.match(r'(周[一二三四五六日])(\d+)$', match_num)
            if m:
                weekday = m.group(1)
                num = m.group(2).zfill(3)
                normalized = f'{weekday}{num}'
                key2 = f'{date}_{normalized}'
                if key2 in league_map:
                    item['league'] = league_map[key2]
                    fixed += 1
                    continue
                
                # Try 2-digit: 周日01
                num2 = m.group(2).zfill(2)
                normalized2 = f'{weekday}{num2}'
                key3 = f'{date}_{normalized2}'
                if key3 in league_map:
                    item['league'] = league_map[key3]
                    fixed += 1
                    continue
            
            # Try with 1-digit
            m = re.match(r'(周[一二三四五六日])(\d+)$', match_num)
            if m:
                weekday = m.group(1)
                num = m.group(2)
                key4 = f'{date}_{weekday}{num}'
                if key4 in league_map:
                    item['league'] = league_map[key4]
                    fixed += 1
                    continue
            
            # Still not found - keep as 未知
            if not current_league:
                item['league'] = '未知'

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
