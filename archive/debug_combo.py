# -*- coding: utf-8 -*-
"""Debug feedback learner combo extraction"""
import os, sys, json, re, glob

# Fix encoding for Windows console
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(path, 'r', encoding='gbk') as f:
                return f.read()
        except:
            return ''

def extract_combo_from_report(report_content):
    combo = {}
    dim_pattern = r'\|\s*(欧赔趋势|竞彩同赔|IW同赔|澳门亚盘|让球同赔|主队主场|客队客场|百家对比|庄家盈亏)\s*\|\s*([+-]?\d+\.\d+)\s+(利好主|利好客|中立)\s*\|\s*(\d+)%'
    dim_map = {
        '欧赔趋势': '欧赔趋势',
        '竞彩同赔': '欧赔趋势',
        'IW同赔': '欧赔趋势',
        '澳门亚盘': '亚盘趋势',
        '让球同赔': '让球趋势',
        '主队主场': '主队主场',
        '客队客场': '客队客场',
        '百家对比': '百家对比',
        '庄家盈亏': '庄家盈亏',
    }
    for m in re.finditer(dim_pattern, report_content):
        dim_name = m.group(1)
        score = float(m.group(2))
        direction = m.group(3)
        weight = int(m.group(4))
        internal_dim = dim_map.get(dim_name, dim_name)
        combo[f'{internal_dim}_score'] = score
        combo[f'{internal_dim}_dir'] = direction
        combo[f'{internal_dim}_weight'] = weight
    m2 = re.search(r'综合信心[:\s]*(\d+)%', report_content)
    if m2:
        combo['confidence'] = int(m2.group(1))
    m3 = re.search(r'\*\*信心\*\*\s*\|\s*(\d+)%', report_content)
    if m3 and 'confidence' not in combo:
        combo['confidence'] = int(m3.group(1))
    return combo

def build_match_map():
    match_map = {}
    for date in sorted(os.listdir(TASKS_DIR)):
        date_dir = os.path.join(TASKS_DIR, date)
        if not os.path.isdir(date_dir):
            continue
        for f in glob.glob(os.path.join(date_dir, '周*.md')):
            m = re.match(r'(周[一二三四五六日]\d+)[_]', os.path.basename(f))
            if m:
                match_num = m.group(1)
                match_map[match_num] = {'report': f, 'date': date, 'dir': os.path.dirname(f)}
        data_dir = os.path.join(date_dir, 'data')
        if os.path.exists(data_dir):
            for md in os.listdir(data_dir):
                md_path = os.path.join(data_dir, md)
                if not os.path.isdir(md_path) or not md.startswith('match'):
                    continue
                meta_file = os.path.join(md_path, 'meta.json')
                if os.path.exists(meta_file):
                    try:
                        meta = json.loads(rd(meta_file))
                        mn = meta.get('matchnum', '')
                        if mn:
                            match_map[mn] = {'report': '', 'date': date, 'dir': md_path, 'meta': meta}
                    except:
                        pass
    return match_map

match_map = build_match_map()
print(f'Total entries in match_map: {len(match_map)}')

# Sample some keys
sample_keys = list(match_map.keys())[:5]
print(f'Sample keys: {sample_keys}')

# Check 2026-05-09 specifically
date = '2026-05-09'
matching = {k: v for k, v in match_map.items() if v.get('date') == date}
print(f'\n2026-05-09 entries in match_map: {len(matching)}')
for k in sorted(matching.keys())[:3]:
    print(f'  {k}: report={os.path.basename(matching[k].get("report", ""))}')

# Check feedback.json match_nums
fb_path = os.path.join(LEARNINGS_DIR, 'feedback.json')
with open(fb_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

dates_data = data.get('dates', data)

# Find 2026-05-09 in feedback
if '2026-05-09' in dates_data:
    matches_0509 = dates_data['2026-05-09'].get('feedback', [])
    print(f'\n2026-05-09 feedback matches: {len(matches_0509)}')
    # Check match_nums
    for m in matches_0509[:3]:
        mn = m.get('match_num', '')
        print(f'  feedback match_num: [{mn}]')
        # Try to find in match_map
        found = False
        for key in match_map:
            if key.endswith(mn) or mn.endswith(key.replace('周六', '').replace('周日', '').replace('周', '')):
                found = True
                print(f'    -> match_map key: {key}')
                break
        if not found:
            print(f'    -> NOT FOUND in match_map')
            print(f'    Available keys ending with {mn}: {[k for k in match_map if k.endswith(mn)][:3]}')

# Now test: try to find a match with a report
print('\n--- Testing report extraction ---')
for date, date_info in list(dates_data.items()):
    matches = date_info.get('feedback', [])
    for m in matches[:1]:
        mn = m.get('match_num', '')
        # Try different formats
        for test_key in [f'周{mn}', mn, f'周X{mn}']:
            for key, val in match_map.items():
                if key.endswith(mn) and mn and key[-3:] == mn:
                    report_path = val.get('report', '')
                    if report_path and os.path.exists(report_path):
                        content = rd(report_path)
                        combo = extract_combo_from_report(content)
                        print(f'  [{date}] {mn} -> {key}: combo keys={list(combo.keys())[:5]}')
                        break
            break
