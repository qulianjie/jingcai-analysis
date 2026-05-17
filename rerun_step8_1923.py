# -*- coding: utf-8 -*-
"""
重新运行 5月5号 第8步 和 19-23步
"""
import os, sys, subprocess, time, json
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = r'jingcai'
DATA_DIR = r'jingcai\tasks\2026-05-05\data'

for d in sorted(os.listdir(DATA_DIR)):
    match_dir = os.path.join(DATA_DIR, d)
    if not os.path.isdir(match_dir):
        continue
    
    meta_file = os.path.join(match_dir, 'meta.json')
    if not os.path.isfile(meta_file):
        continue
    
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    match_num = meta.get('matchnum', '')
    macau = meta.get('macau_line', '')
    
    print(f"\n{'='*50}")
    print(f"[{match_num}] {d}")
    print(f"  macau_line = {macau}")
    
    # Run step8_1923_extractor
    print(f"  Running step8_1923_extractor...")
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), match_dir],
            capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace'
        )
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-5:]:
                print(f"    {line.strip()}")
        if result.returncode != 0 and result.stderr:
            print(f"    ERR: {result.stderr[:300]}")
    except Exception as e:
        print(f"    ERROR: {e}")
    
    time.sleep(1)
