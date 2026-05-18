import os, sys, json, re

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
DATA_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16/data')
PYTHON = sys.executable

# Find all incomplete dirs
incomplete = []
for d in sorted(os.listdir(DATA_DIR)):
    if not d.startswith('match') or not os.path.isdir(os.path.join(DATA_DIR, d)):
        continue
    dp = os.path.join(DATA_DIR, d)
    mp = os.path.join(dp, 'meta.json')
    if os.path.exists(mp):
        with open(mp, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        mn = meta.get('matchnum', '')
        n = re.search(r'(\d{3})$', mn)
        if n:
            num = n.group(1)
            s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
            s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
            s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
            s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
            ok = s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0
            if not ok:
                incomplete.append((num, d))

print('Incomplete: {} matches'.format(len(incomplete)))

# Fix each one
for num, d in incomplete:
    dp = os.path.join(DATA_DIR, d)
    print('\n[{}] {}'.format(num, d[:40]))
    
    scripts = [
        'step146_extractor.py',
        'step235_runner.py',
        'step7_runner.py',
        'step8_1923_extractor.py',
        'step918_extractor.py',
        'step24_extractor.py',
    ]
    
    for s in scripts:
        cmd = '{} {} {}'.format(PYTHON, os.path.join(SCRIPT_DIR, s), dp)
        print('  {}'.format(s))
        ret = os.system(cmd)
    
    # Report
    cmd = '{} {} {}'.format(PYTHON, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), dp)
    print('  report')
    os.system(cmd)

# Clean duplicate 008
import re as re_mod
seen = {}
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16')
for f in sorted(os.listdir(TASKS_DIR)):
    if f.endswith('.md') and f.startswith('周日'):
        n = re_mod.search(r'(\d{3})', f)
        if n:
            num = n.group(1)
            fp = os.path.join(TASKS_DIR, f)
            if num in seen:
                os.remove(fp)
                print('Removed dup: {}'.format(f))
            else:
                seen[num] = fp

print('\nDone')
