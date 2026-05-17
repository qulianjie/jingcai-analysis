import subprocess
import sys
import time
import os

SCRIPT = r'C:\Users\lianjie\.openclaw\workspace\jingcai\run_pipeline.py'
LOCK = r'C:\Users\lianjie\.openclaw\workspace\jingcai\.locks\pipeline.lock'
DATE = '2026-05-10'
MATCHES = ['003','004','005','006','007','008']

def force_unlock():
    if os.path.exists(LOCK):
        try:
            os.remove(LOCK)
            print('[unlock] lock file removed')
        except:
            pass

for match in MATCHES:
    print(f'\n{"="*60}')
    print(f'>>> Running {match}...')
    print(f'{"="*60}')
    force_unlock()
    time.sleep(1)
    result = subprocess.run(
        [sys.executable, SCRIPT, DATE, match],
        timeout=600
    )
    print(f'>>> {match} done (rc={result.returncode})')
    force_unlock()
    time.sleep(3)

print('\n=== All done! ===')
