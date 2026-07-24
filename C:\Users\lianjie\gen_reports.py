import os, json, subprocess, sys

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-07-16\data'
report_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-07-16'
generator = r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_report_generator.py'
python = r'C:\Python314\python.exe'

for d in sorted(os.listdir(base)):
    if not d.startswith('match'):
        continue
    dp = os.path.join(base, d)
    meta_path = os.path.join(dp, 'meta.json')
    if not os.path.exists(meta_path):
        continue
    
    with open(meta_path) as f:
        meta = json.load(f)
    
    mn = meta.get('matchnum', '')
    home = meta.get('home', '')
    away = meta.get('away', '')
    output = os.path.join(report_dir, f'{mn}_{home}vs{away}.md')
    
    if os.path.exists(output) and os.path.getsize(output) > 10000:
        print(f'[跳过] {mn} {home}vs{away} ({os.path.getsize(output)} bytes)')
        continue
    
    print(f'[生成] {mn} {home}vs{away}...', end=' ', flush=True)
    ret = subprocess.run(
        [python, generator, dp, output],
        capture_output=True, text=True, timeout=120
    )
    if os.path.exists(output):
        sz = os.path.getsize(output)
        if sz > 1000:
            print(f'OK {sz} bytes')
        else:
            print(f'小文件 {sz} bytes')
    else:
        print(f'失败')
        if ret.stderr:
            print(f'  stderr: {ret.stderr[:200]}')

print()
print('=== 报告列表 ===')
for f in sorted(os.listdir(report_dir)):
    if f.endswith('.md') and 'sunday' not in f and 'monday' not in f:
        sz = os.path.getsize(os.path.join(report_dir, f))
        print(f'  {f}: {sz} bytes')
