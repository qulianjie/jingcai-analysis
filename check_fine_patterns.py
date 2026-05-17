# -*- coding: utf-8 -*-
"""Check what fine-grained data is available for fine pattern matching"""
import os, sys, json, glob, re

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

# Load feedback
with open(os.path.join(LEARNINGS_DIR, 'feedback.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

dates_data = data.get('dates', data)

# Build match_map
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
                        if mn in match_map and match_map[mn].get('report'):
                            match_map[mn]['dir'] = md_path
                        else:
                            match_map[mn] = {'report': '', 'date': date, 'dir': md_path, 'meta': meta}
                except:
                    pass

# Normalize
for key, val in list(match_map.items()):
    if key.startswith('周') and len(key) >= 4:
        num_part = key[3:]
        if num_part not in match_map:
            match_map[num_part] = val

# Count available data
has_s25 = 0
has_s26 = 0
has_asian_odds = 0
has_handicap_odds = 0
has_report = 0
sample_count = 0

# Scan a few dates for data exploration
for date in ['2026-05-03', '2026-05-04', '2026-05-05', '2026-05-06']:
    date_dir = os.path.join(TASKS_DIR, date)
    if not os.path.isdir(date_dir):
        continue
    data_dir = os.path.join(date_dir, 'data')
    if not os.path.exists(data_dir):
        continue
    
    # Check report file
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        content = rd(f)
        if content:
            has_report += 1
            # Check what's in the report
            # Look for Asian handicap info
            asian_m = re.search(r'澳门即时[：:]\s*(.+)', content)
            if asian_m:
                print(f'  [{date}] Report Asian: {asian_m.group(1).strip()[:50]}')
            
            # Look for handicap line
            hc_m = re.search(r'让球[：:]\s*(.+)', content)
            if hc_m:
                print(f'  [{date}] Report Handicap: {hc_m.group(1).strip()[:50]}')
            
            # Look for 欧赔 line
            ou_m = re.search(r'欧赔[（(].*[）)]\s*[：:]\s*(.+)', content)
            if ou_m:
                print(f'  [{date}] Report Oupi: {ou_m.group(1).strip()[:50]}')
    
    # Check match data dirs
    for md in sorted(os.listdir(data_dir))[:3]:
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        
        s25 = os.path.join(md_path, 'step25_zhuangjia.json')
        s26 = os.path.join(md_path, 'step26_profit_ratio.json')
        
        if os.path.exists(s25):
            has_s25 += 1
            s25_data = json.loads(rd(s25))
            if sample_count == 0:
                print(f'\n  step25 structure:')
                print(f'    data keys: {list(s25_data.get("data", {}).keys())}')
                for k, v in s25_data.get("data", {}).items():
                    print(f'    {k}: {json.dumps(v, ensure_ascii=False)}')
                print(f'    conclusion: {json.dumps(s25_data.get("conclusion", {}), ensure_ascii=False)}')
        
        if os.path.exists(s26):
            has_s26 += 1
            s26_data = json.loads(rd(s26))
            if sample_count == 0:
                print(f'\n  step26 analysis:')
                analysis = s26_data.get('analysis', {})
                print(f'    {json.dumps(analysis, ensure_ascii=False)}')
                print(f'    profit_ratio:')
                for k, v in s26_data.get('profit_ratio', {}).items():
                    print(f'      {k}: {json.dumps(v, ensure_ascii=False)}')
        
        sample_count += 1

print(f'\n  Has s25: {has_s25}, Has s26: {has_s26}, Has report: {has_report}')
print(f'  Total match_map entries: {len(match_map)}')
