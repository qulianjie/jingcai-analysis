import os, sys, subprocess, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16')
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Find match27 dir
for d in os.listdir(DATA_DIR):
    if not d.startswith('match27'):
        continue
    dp = os.path.join(DATA_DIR, d)
    print(f'Dir: {dp}')
    
    scripts = [
        'step235_runner.py',
        'step7_runner.py',
        'step8_1923_extractor.py',
        'step918_extractor.py',
        'step24_extractor.py',
    ]
    
    for s in scripts:
        print(f'  -> {s}...')
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, s), dp],
                timeout=1800, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(f'  rc={r.returncode}')
        except Exception as e:
            print(f'  ERROR: {e}')
        time.sleep(2)
    
    # Report
    print('  -> report...')
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), dp],
            timeout=300, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        print(f'  ERROR: {e}')
