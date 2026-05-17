# -*- coding: utf-8 -*-
"""Quick test: run all steps for match1 only, check step8 and step19 output"""
import os, sys, json, subprocess
from datetime import datetime

os.chdir('C:/Users/lianjie/.openclaw/workspace/jingcai')

os.environ['PYTHONIOENCODING'] = 'utf-8'

DATE = '2026-05-16'
TASKS_DIR = 'tasks/{}'.format(DATE)
MATCH_DIR = os.path.join(TASKS_DIR, '周六001_水户蜀葵vs东京绿茵')

print('=== Match Dir ===')
print(MATCH_DIR)
print('Exists:', os.path.isdir(MATCH_DIR))

# Read meta
if os.path.exists(os.path.join(MATCH_DIR, 'meta.json')):
    with open(os.path.join(MATCH_DIR, 'meta.json'), 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print('Meta:', json.dumps(meta, ensure_ascii=False, indent=2)[:500])
else:
    print('No meta.json!')
    sys.exit(1)

home_id = meta.get('home_id', '')
away_id = meta.get('away_id', '')
league = meta.get('league', '')
fid = meta.get('fid', '')
macau_line = meta.get('macau_line', '')

print('home_id:', home_id)
print('away_id:', away_id)
print('league:', league)
print('fid:', fid)
print('macau_line:', macau_line)

if not home_id or not away_id:
    print('Need home_id/away_id, running step146...')
    ret = os.system('{} step146_extractor.py "{}"'.format(sys.executable, MATCH_DIR))
    print('step146 RC:', ret)
    
    with open(os.path.join(MATCH_DIR, 'meta.json'), 'r', encoding='utf-8') as f:
        meta = json.load(f)
    home_id = meta.get('home_id', '')
    away_id = meta.get('away_id', '')
    league = meta.get('league', '')
    fid = meta.get('fid', '')
    macau_line = meta.get('macau_line', '')
    print('After step146 - home_id:', home_id, 'away_id:', away_id)

# Step 2
print('\n=== Step 2: 竞彩同赔 ===')
ret = os.system('{} step235_runner.py {} {} jingcai group01_europe/step02_jingcai_same.txt'.format(sys.executable, home_id, away_id, league))
print('RC:', ret)

# Step 8 + 19-23
print('\n=== Step 8 + 19-23 ===')
ret = os.system('{} step8_1923_extractor.py "{}"'.format(sys.executable, MATCH_DIR))
print('RC:', ret)

# Check results
print('\n=== Step 8 Result ===')
step8_path = os.path.join(MATCH_DIR, 'group03_asian', 'step8_same_league.txt')
if os.path.exists(step8_path):
    with open(step8_path, 'r', encoding='utf-8') as f:
        content = f.read()
    rows = [l for l in content.split('\n') if '|' in l and '同联赛' not in l.lower() and '---' not in l]
    print('File size:', len(content), 'bytes')
    print('Rows with |:', len(rows))
    for row in rows[:5]:
        print(' ', row.strip()[:100])
else:
    print('File not found!')

print('\n=== Step 19 Result ===')
step19_path = os.path.join(MATCH_DIR, 'group06_baijia', 'step19_baijia_compare.txt')
if os.path.exists(step19_path):
    with open(step19_path, 'r', encoding='utf-8') as f:
        content = f.read()
    rows = [l for l in content.split('\n') if '|' in l]
    print('File size:', len(content), 'bytes')
    print('Rows with |:', len(rows))
    for row in rows[:5]:
        print(' ', row.strip()[:100])
else:
    print('File not found!')

# Step 9-18
print('\n=== Step 9-18 ===')
ret = os.system('{} step918_extractor.py {} {} {} {} "{}"'.format(sys.executable, home_id, away_id, league, fid, MATCH_DIR))
print('RC:', ret)

# Step 24
print('\n=== Step 24 ===')
ret = os.system('{} step24_extractor.py "{}"'.format(sys.executable, MATCH_DIR))
print('RC:', ret)

print('\n=== DONE ===')
