import subprocess
import sys
import os

dates = ['2026-05-07','2026-05-08','2026-05-09','2026-05-10','2026-05-11','2026-05-12','2026-05-13','2026-05-14','2026-05-15']

script_dir = os.path.dirname(os.path.abspath(__file__))
run_script = os.path.join(script_dir, 'run_pipeline.py')

processes = []
for d in dates:
    print('Starting: {}'.format(d))
    p = subprocess.Popen(
        [sys.executable, run_script, d],
        cwd=script_dir,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    processes.append((d, p))
    print('  PID {} -> {}'.format(p.pid, d))

print('\nAll {} pipelines started'.format(len(processes)))
print('Waiting for completion...')

completed = 0
for d, p in processes:
    p.wait()
    completed += 1
    print('[{}/{}] {} completed (exit={})'.format(completed, len(processes), d, p.returncode))

print('\nAll done!')
