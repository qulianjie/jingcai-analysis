import os, sys

TASKS_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Check match24
d = os.path.join(DATA_DIR, 'match24_博德闪耀__特罗姆瑟')
if os.path.exists(d):
    print('match24 EXISTS')
    for root, dirs, files in os.walk(d):
        for f in files:
            fp = os.path.join(root, f)
            size = os.path.getsize(fp)
            rel = os.path.relpath(fp, d)
            print(f'  {rel}: {size}B')
else:
    print('match24 NOT FOUND')
    # Find it by name pattern
    for entry in os.listdir(DATA_DIR):
        if entry.startswith('match24'):
            print(f'Found: {entry}')

# List all report files
print('\n=== Reports ===')
for f in sorted(os.listdir(TASKS_DIR)):
    if f.endswith('.md') and not f.startswith('summary') and f != 'sunday_matches.md':
        size = os.path.getsize(os.path.join(TASKS_DIR, f))
        print(f'  {f[:60]:60s} {size}B')
