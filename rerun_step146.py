import os, sys, json, subprocess

DATA_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-13/data'
SCRIPT = 'C:/Users/lianjie/.openclaw/workspace/jingcai/step146_extractor.py'

for d in sorted(os.listdir(DATA_DIR)):
    dp = os.path.join(DATA_DIR, d)
    if not os.path.isdir(dp):
        continue
    meta_file = os.path.join(dp, 'meta.json')
    if not os.path.exists(meta_file):
        print('SKIP %s (no meta.json)' % d)
        continue
    
    print('=== %s ===' % d)
    result = subprocess.run([sys.executable, SCRIPT, dp], capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print('ERROR: %s' % result.stderr.strip())
    print()
