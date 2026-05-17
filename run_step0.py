# -*- coding: utf-8 -*-
import subprocess, sys, os, json

os.chdir('C:/Users/lianjie/.openclaw/workspace/jingcai')

# Step 0
print('=== Step 0: Fetch matches ===')
result = subprocess.run(
    [sys.executable, 'step0_fetch_matches.py', '2026-05-16'],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout[:2000] if result.stdout else '(no stdout)')
if result.stderr:
    print('STDERR:', result.stderr[:500])
print('RC:', result.returncode)

# Check
if os.path.exists('tasks/2026-05-16/data/matches_data.json'):
    with open('tasks/2026-05-16/data/matches_data.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)
    print(f'\nMatches found: {len(matches)}')
    for m in matches:
        print(f"  {m.get('seq','')}: {m.get('home','')} vs {m.get('away','')} ({m.get('league','')})")
else:
    print('\nNo matches_data.json found!')
