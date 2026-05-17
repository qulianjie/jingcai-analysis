import sys, os
sys.stdout.reconfigure(encoding='utf-8')

data_dir = r'jingcai\tasks\2026-05-12\data'
for d in sorted(os.listdir(data_dir)):
    if not d.startswith('match'): continue
    mp = os.path.join(data_dir, d, 'meta.json')
    if not os.path.exists(mp): continue
    import json
    with open(mp, encoding='utf-8') as f:
        meta = json.load(f)
    mn = meta.get('matchnum', '')
    
    step4 = os.path.join(data_dir, d, 'group02_handicap', 'step4_handicap_base.txt')
    if os.path.exists(step4):
        with open(step4, encoding='utf-8') as f:
            content = f.read()
        for line in content.split('\n'):
            if '竞彩官方' in line and '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                print(f'{mn} | {d} | parts={parts}')
                break
