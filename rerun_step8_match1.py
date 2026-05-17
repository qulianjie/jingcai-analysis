# -*- coding: utf-8 -*-
"""Re-run step8 for match1 (日职) to test fix"""
import os, sys, json

# Find match1 directory
data_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(data_dir)):
    if not os.path.isdir(os.path.join(data_dir, x)):
        continue
    if 'match1_' in x and not x.startswith('match10') and not x.startswith('match11') and not x.startswith('match12') and not x.startswith('match13') and not x.startswith('match14') and not x.startswith('match15') and not x.startswith('match16') and not x.startswith('match17') and not x.startswith('match18') and not x.startswith('match19'):
        match_dir = os.path.join(data_dir, x)
        meta_path = os.path.join(match_dir, 'meta.json')
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print(f'Re-running step8 for: {x}')
        print(f'League: {meta.get("league", "")}')
        print(f'Macau line: {meta.get("macau_line", "")}')
        
        # Run step8_1923_extractor.py
        script_path = 'C:/Users/lianjie/.openclaw/workspace/jingcai/step8_1923_extractor.py'
        
        import subprocess
        result = subprocess.run(
            [sys.executable, script_path, match_dir],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace'
        )
        
        print('STDOUT:')
        print(result.stdout[:2000])
        if result.stderr:
            print('STDERR:')
            print(result.stderr[:500])
        print(f'Return code: {result.returncode}')
        
        # Check output file
        step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
        if os.path.exists(step8_path):
            with open(step8_path, 'r', encoding='utf-8') as f:
                content = f.read()
            rows = [l for l in content.split('\n') if l.startswith('|') and '---' not in l and '序号' not in l]
            print(f'\nStep8 output: {len(rows)} table rows')
        
        break
