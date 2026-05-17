import subprocess
import sys
import time

SCRIPT = r'C:\Users\lianjie\.openclaw\workspace\jingcai\run_pipeline.py'
DATE = '2026-05-10'
MATCHES = ['001','002','003','004','005','006','007','008']

for match in MATCHES:
    print(f'\n{"="*60}')
    print(f'Running match {match}...')
    print(f'{"="*60}')
    result = subprocess.run(
        [sys.executable, SCRIPT, DATE, match],
        timeout=600
    )
    print(f'Match {match} completed with returncode={result.returncode}')
    time.sleep(5)

print('\nAll matches done!')
