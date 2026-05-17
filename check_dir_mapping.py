import os, json, re

DATA_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])

print('现有目录:')
for d in dirs:
    meta_path = os.path.join(DATA_DIR, d, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        matchnum = meta.get('matchnum', '?')
        # Extract 3-digit number
        m2 = re.search(r'(\d{3})$', matchnum)
        num = m2.group(1) if m2 else '?'
        home = meta.get('home', '')
        away = meta.get('away', '')
        print(f'  {d[:40]:40s} -> {num}: {home} vs {away}')
