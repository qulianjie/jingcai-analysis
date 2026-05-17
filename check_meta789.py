import os, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted([d for d in os.listdir(base) if d.startswith('match')])

for d in dirs:
    if d.startswith('match7_') or d.startswith('match8_') or d.startswith('match9_'):
        meta_path = os.path.join(base, d, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f"=== {d} ===")
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            print()
