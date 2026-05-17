import os, sys, json, subprocess, time

SCRIPT_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai'
DATA_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16/data')

dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])

for d in dirs:
    if not d.startswith('match9_'):
        continue
    
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    if not os.path.exists(meta_path):
        print('SKIP: no meta.json')
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    print('Retry: ' + d)
    print('  matchnum: ' + meta.get('matchnum', '?'))
    print('  league: ' + meta.get('league', ''))
    print('  home_id: ' + meta.get('home_id', '') + ', away_id: ' + meta.get('away_id', ''))
    print('  macau_line: ' + meta.get('macau_line', ''))
    print()
    
    # Step 8 + 19-23
    s8_path = os.path.join(dp, 'group03_asian/step8_same_league.txt')
    if not os.path.exists(s8_path) or os.path.getsize(s8_path) < 500:
        print('  -> running step8+19-23...')
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), dp]
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            print('  step8+19-23: return=' + str(r.returncode))
        except subprocess.TimeoutExpired:
            print('  step8+19-23: timeout')
        except Exception as e:
            print('  step8+19-23: ERROR: ' + str(e))
        time.sleep(2)
    else:
        print('  step8 already exists: ' + str(os.path.getsize(s8_path)) + 'B')
    
    # Step 9-18
    s9_path = os.path.join(dp, 'group04_teamA/step9_home_history.txt')
    if not os.path.exists(s9_path) or os.path.getsize(s9_path) < 500:
        print('  -> running step9-18...')
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step918_extractor.py'), dp]
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            print('  step9-18: return=' + str(r.returncode))
        except subprocess.TimeoutExpired:
            print('  step9-18: timeout')
        except Exception as e:
            print('  step9-18: ERROR: ' + str(e))
        time.sleep(2)
    else:
        print('  step9 already exists: ' + str(os.path.getsize(s9_path)) + 'B')
    
    # Verify
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian/step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) else 0
    
    ok = s8 > 500 and s9 > 500 and s14 > 500 and s19 > 500
    print('')
    print('  Result: ' + ('OK' if ok else 'MISS') + ' s8=' + str(s8) + 'B s9=' + str(s9) + 'B s14=' + str(s14) + 'B s19=' + str(s19) + 'B')
