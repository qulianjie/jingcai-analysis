# -*- coding: utf-8 -*-
"""Debug: check why fix_league5 finds 0 matches"""
import json, os, re

FB = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Build league map
league_map = {}
for date_dir in sorted(os.listdir(TASKS_DIR)):
    if not re.match(r'\d{4}-\d{2}-\d{2}', date_dir):
        continue
    task_path = os.path.join(TASKS_DIR, date_dir)
    if not os.path.isdir(task_path):
        continue
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
                    matchnum = meta.get('matchnum', '')
                    league = meta.get('league', '')
                    if matchnum and league:
                        num_match = re.search(r'(\d+)', matchnum)
                        if num_match:
                            num = num_match.group(1).zfill(3)
                            key = (date_dir, num)
                            league_map[key] = league
                except:
                    continue

print('league_map sample keys:')
for k in list(league_map.keys())[:10]:
    print('  %s' % str(k))

# Check feedback entries with empty league
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)
dates = data.get('dates', {})

print()
print('Feedback entries with empty/unknown league:')
for date, date_data in sorted(dates.items()):
    for item in date_data.get('feedback', []):
        current_league = item.get('league', '')
        if not current_league or current_league == '未知':
            match_num = item.get('match_num', '')
            num_match = re.search(r'(\d+)', match_num)
            if num_match:
                num = num_match.group(1).zfill(3)
            else:
                num = ''
            key = (date, num)
            in_map = key in league_map
            print('  date=%s match_num=%s num=%s key=%s in_map=%s' % (date, match_num, num, str(key), in_map))
            break  # Just show first one per date
