# -*- coding: utf-8 -*-
"""修复feedback.json中缺失的league字段 - 从match目录的meta.json补回"""
import json, os, re

FB = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Step 1: Build league map from all meta.json files
meta_league_map = {}
for date_dir in sorted(os.listdir(TASKS_DIR)):
    if not re.match(r'\d{4}-\d{2}-\d{2}', date_dir):
        continue
    task_path = os.path.join(TASKS_DIR, date_dir)
    if not os.path.isdir(task_path):
        continue
    
    # Check data/match* directories
    data_path = os.path.join(task_path, 'data')
    if os.path.isdir(data_path):
        for subdir in os.listdir(data_path):
            if not re.match(r'match\d+|match\d+__', subdir):
                continue
            meta_path = os.path.join(data_path, subdir, 'meta.json')
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    mi = meta.get('match_info', {})
                    week = mi.get('week', '')  # e.g. "周日"
                    match_no = mi.get('match_no', '').zfill(3)  # e.g. "001"
                    league = mi.get('league', '')
                    if not league:
                        league = meta.get('league', '')
                    if week and match_no and league:
                        key = f'{date_dir}_{week}{match_no}'
                        meta_league_map[key] = league
                except:
                    continue
    
    # Also check .md files for league info
    for fname in os.listdir(task_path):
        if fname.endswith('.md'):
            fpath = os.path.join(task_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                m = re.search(r'(周[一二三四五六日]\d+)\s*', content[:100])
                if m:
                    mn = m.group(1)
                    # Find league from header
                    m2 = re.search(r'联赛[:\s]+([^\n·]+)', content[:1000])
                    if not m2:
                        # Try from title
                        m2 = re.search(r'#\s*(?:周[一二三四五六日]\d+_)?[^v]*vs', content[:500])
                    if m2:
                        league_text = m2.group(0)
                        # Extract league from the report header section
                        header_section = content[:2000]
                        lm = re.search(r'[:\s]+(英超|西甲|德甲|意甲|法甲|荷甲|葡超|俄超|比甲|瑞士超|挪超|瑞典超|芬超|丹超|苏超|澳超|日职|日联|韩职|沙特职业联赛|英冠|西甲|土超|阿甲|巴甲|中超|美职联|墨超|解放者杯|欧冠|欧联|欧协联|世界杯|欧洲杯|美洲杯|亚洲杯|非洲杯|友谊赛|欧冠杯|欧会杯|球会友谊)[\s·:]', header_section)
                        if lm:
                            key = f'{date_dir}_{mn}'
                            if key not in meta_league_map:
                                meta_league_map[key] = lm.group(1)
            except:
                continue

print('Built meta_league_map: %d entries' % len(meta_league_map))
print('Sample:')
for k, v in list(meta_league_map.items())[:10]:
    print('  %s -> %s' % (k, v))

# Step 2: Fix feedback.json
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)

dates = data.get('dates', {})
fixed = 0

for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        if item.get('league', ''):
            continue  # already has league
        
        match_num = item.get('match_num', '')
        key = f'{date}_{match_num}'
        
        if key in meta_league_map:
            item['league'] = meta_league_map[key]
            fixed += 1
        else:
            # Try to find via partial match
            for mk, ml in meta_league_map.items():
                if mk.startswith(date + '_') and match_num in mk:
                    item['league'] = ml
                    fixed += 1
                    break
            else:
                # If still not found, mark as 未知
                item['league'] = '未知'

# Save
with open(FB, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Fixed: %d entries' % fixed)

# Step 3: Verify
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)
dates = data.get('dates', {})
league_counts = {}
total = 0
for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        total += 1
        league = item.get('league', '')
        if not league:
            league = '(empty)'
        league_counts[league] = league_counts.get(league, 0) + 1

print()
print('Total: %d' % total)
print('Unknown: %d' % league_counts.get('未知', 0))
print('Empty: %d' % league_counts.get('(empty)', 0))
print('League distribution:')
for league, count in sorted(league_counts.items(), key=lambda x: -x[1])[:20]:
    print('  %s: %d' % (league, count))
