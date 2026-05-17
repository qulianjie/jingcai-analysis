import os, json

d = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(d))[:5]:
    if os.path.isdir(os.path.join(d, x)):
        meta_path = os.path.join(d, x, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f'{x}: league={meta.get("league", "")}, macau_line={meta.get("macau_line", "")}')
