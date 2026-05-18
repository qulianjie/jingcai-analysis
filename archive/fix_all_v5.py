import os, sys, json, re

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Load matches
with open(os.path.join(TASKS_DIR, 'matches_data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])

match_map = {}
for m in all_matches:
    num_raw = m.get('matchnum', '')
    m2 = re.search(r'(\d{3})$', num_raw)
    if m2:
        match_map[m2.group(1)] = m

# Build map
dir_map = {}
for d in os.listdir(DATA_DIR):
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
            if num not in dir_map or (ok and not dir_map[num][1]):
                dir_map[num] = (d, ok)

# What needs fixing
needs = []
for num in sorted(match_map.keys()):
    if num not in dir_map:
        needs.append(('CREATE', num))
    elif not dir_map[num][1]:
        needs.append(('FIX', num))

print('Need to fix: {} matches'.format(len(needs)))
for t, n in needs:
    m = match_map[n]
    print('  {}: {} - {} vs {}'.format(t, n, m.get('home',''), m.get('away','')))

# Max dir number
max_n = max([int(d.split('_')[0].replace('match','')) for d in os.listdir(DATA_DIR) if d.startswith('match')])
next_n = max_n + 1

# Write a batch file to fix each match
bat_lines = ['@echo off', 'cd /d {}'.format(SCRIPT_DIR)]

for typ, num in needs:
    m = match_map[num]
    home = m.get('home', '')
    away = m.get('away', '')
    
    if typ == 'CREATE':
        dn = 'match{}_{}__{}'.format(next_n, home, away)
        match_dir = os.path.join(DATA_DIR, dn)
        os.makedirs(match_dir, exist_ok=True)
        with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'matchnum': m.get('matchnum',''),
                'match': '{} {} vs {}'.format(m.get('matchnum',''), home, away),
                'fid': m.get('fid',''), 'league': m.get('league',''),
                'home': home, 'away': away, 'date': '2026-05-16',
                'status': 'in_progress',
                'home_id': m.get('home_id',''), 'away_id': m.get('away_id',''),
                'rq': m.get('rq',''), 'macau_line': m.get('macau_line',''),
            }, f, ensure_ascii=False, indent=2)
        next_n += 1
    else:
        match_dir = os.path.join(DATA_DIR, dir_map[num][0])
    
    bat_lines.append('echo [{num}] {name}'.format(num=num, name=os.path.basename(match_dir)))
    
    scripts = ['step146_extractor.py', 'step235_runner.py', 'step7_runner.py', 
               'step8_1923_extractor.py', 'step918_extractor.py', 'step24_extractor.py']
    
    for script in scripts:
        bat_lines.append('echo   {}...'.format(script))
        bat_lines.append('{} {} {}'.format(sys.executable, os.path.join(SCRIPT_DIR, script), match_dir))
        bat_lines.append('timeout /t 1 /nobreak >nul')
    
    bat_lines.append('echo   report...')
    bat_lines.append('{} {} {}'.format(sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir))
    bat_lines.append('timeout /t 1 /nobreak >nul')

# Clean duplicate reports
seen = {}
for f in sorted(os.listdir(TASKS_DIR)):
    if f.endswith('.md') and f.startswith('周日'):
        n = re.search(r'(\d{3})', f)
        if n:
            num = n.group(1)
            fp = os.path.join(TASKS_DIR, f)
            if num in seen:
                os.remove(fp)
                print('Removed dup: {}'.format(f))
            else:
                seen[num] = fp

bat_lines.append('echo Done. {} unique reports'.format(len(seen)))

bat_file = os.path.join(SCRIPT_DIR, 'fix_bat.bat')
with open(bat_file, 'w', encoding='gbk') as f:
    f.write('\n'.join(bat_lines))

print('Batch file written: {}'.format(bat_file))
print('Run: {}'.format(bat_file))
