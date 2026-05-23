# -*- coding: utf-8 -*-
"""同步剩余日期到Notion，使用更长超时"""
import os, sys, subprocess, time

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
SCRIPTS = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# Already synced: 04-01, 04-02, 04-29, 04-30, 05-03, 05-04
# Need to sync: 05-01, 05-02, 05-05, 05-06, 05-07, 05-08, 05-09, 05-10, 05-11, 05-12, 05-13
# Also: 05-14, 05-15, 05-16, 05-17, 05-18, 05-19

remaining = ['2026-05-01','2026-05-02','2026-05-05','2026-05-06','2026-05-07',
             '2026-05-08','2026-05-09','2026-05-10','2026-05-11','2026-05-12',
             '2026-05-13','2026-05-14','2026-05-15','2026-05-16','2026-05-17',
             '2026-05-18','2026-05-19']

sync_ok = 0
sync_fail = 0

for date_str in remaining:
    print(f'\n同步 {date_str}...', end=' ', flush=True)
    try:
        r = subprocess.run(
            ['node', os.path.join(SCRIPTS, 'pipeline.js'), 'sync', date_str],
            timeout=900, encoding='utf-8', errors='replace',
            creationflags=0x08000000, cwd=SCRIPTS
        )
        if r.returncode == 0:
            print(f'✅')
            sync_ok += 1
        else:
            print(f'❌ (rc={r.returncode})')
            sync_fail += 1
    except subprocess.TimeoutExpired:
        print(f'⏰ 超时')
        sync_fail += 1
    except Exception as e:
        print(f'❌ {e}')
        sync_fail += 1
    time.sleep(3)

print(f'\n{"="*50}')
print(f'同步完成: 成功 {sync_ok}, 失败 {sync_fail}')
print(f'{"="*50}')
