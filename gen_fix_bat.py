import os, sys, json, re

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
DATA_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16/data')

# Find all match dirs and their status
print('=== Match dir status ===')
dir_status = {}
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
            s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
            ok = s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24
            status = 'OK' if ok else 'INCOMPLETE'
            if num not in dir_status or (ok and not dir_status[num][1]):
                dir_status[num] = (d, status, dp)
            print('  {} {} {}'.format(num, d[:50], status))

# Write batch file
bat_lines = ['@echo off', 'cd /d {}'.format(SCRIPT_DIR)]
PYTHON = sys.executable

incomplete = [(num, d, dp) for num, (d, status, dp) in sorted(dir_status.items()) if status == 'INCOMPLETE']
print('\nIncomplete: {}'.format([num for num, d, dp in incomplete]))

for num, d, dp in incomplete:
    bat_lines.append('echo [{}] {}'.format(num, d[:40]))
    
    scripts = [
        'step146_extractor.py',
        'step235_runner.py', 
        'step7_runner.py',
        'step8_1923_extractor.py',
        'step918_extractor.py',
        'step24_extractor.py',
    ]
    
    for s in scripts:
        bat_lines.append('echo   {}...'.format(s))
        bat_lines.append('{} {} {}'.format(PYTHON, os.path.join(SCRIPT_DIR, s), dp))
        bat_lines.append('timeout /t 1 /nobreak >nul')
    
    bat_lines.append('echo   report...')
    bat_lines.append('{} {} {}'.format(PYTHON, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), dp))
    bat_lines.append('timeout /t 1 /nobreak >nul')

bat_lines.append('echo Done')

bat_file = os.path.join(SCRIPT_DIR, 'run_fix.bat')
with open(bat_file, 'w', encoding='gbk') as f:
    f.write('\r\n'.join(bat_lines))

print('Batch file: {}'.format(bat_file))
print('Run: cmd /c {}'.format(bat_file))
