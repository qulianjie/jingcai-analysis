import os, sys, json, subprocess, time

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')
DETACHED = getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)

scripts = [
    'step146_extractor.py',
    'step235_runner.py',
    'step7_runner.py',
    'step8_1923_extractor.py',
    'step918_extractor.py',
    'step24_extractor.py',
]

# Fix match28 (029) - New York Red Bulls vs New York City
d28 = os.path.join(DATA_DIR, 'match28_纽约红牛__纽约城')
print('Fixing match28 (029)...')
for s in scripts:
    print('  -> {}'.format(s))
    try:
        subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, s), d28],
            cwd=SCRIPT_DIR,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=DETACHED, timeout=300
        )
    except Exception as e:
        print('    ERROR: {}'.format(e))
    time.sleep(1)

# Report
print('  -> report...')
try:
    subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), d28],
        cwd=SCRIPT_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=DETACHED, timeout=300
    )
except Exception as e:
    print('    ERROR: {}'.format(e))

time.sleep(1)

# Fix match30 (030) - Inter Miami vs Atlanta United
d30 = os.path.join(DATA_DIR, 'match30_国际迈阿密__亚特兰大联')
print('Fixing match30 (030)...')
for s in scripts:
    print('  -> {}'.format(s))
    try:
        subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, s), d30],
            cwd=SCRIPT_DIR,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=DETACHED, timeout=300
        )
    except Exception as e:
        print('    ERROR: {}'.format(e))
    time.sleep(1)

# Report
print('  -> report...')
try:
    subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), d30],
        cwd=SCRIPT_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=DETACHED, timeout=300
    )
except Exception as e:
    print('    ERROR: {}'.format(e))

# Clean duplicate 008 report
import re
seen = {}
for f in sorted(os.listdir(TASKS_DIR)):
    if f.endswith('.md') and f.startswith('周日'):
        n = re.search(r'(\d{3})', f)
        if n:
            num = n.group(1)
            fp = os.path.join(TASKS_DIR, f)
            if num in seen:
                os.remove(fp)
                print('Removed dup: {}'.format(f))
            else:
                seen[num] = fp

print('Done')
