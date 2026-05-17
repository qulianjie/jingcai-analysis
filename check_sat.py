# -*- coding utf-8 -*-
import json, os

data = json.load(open('jingcai/tasks/2026-05-09/matches_data.json', 'r', encoding='utf-8'))
sat = data['groups']['周六']['matches']
task_dir = 'jingcai/tasks/2026-05-09'
data_dir = os.path.join(task_dir, 'data')

# Check existing data directories
existing_dirs = set()
if os.path.exists(data_dir):
    for d in os.listdir(data_dir):
        if d.startswith('match'):
            meta_path = os.path.join(data_dir, d, 'meta.json')
            if os.path.exists(meta_path):
                meta = json.load(open(meta_path, 'r', encoding='utf-8'))
                existing_dirs.add(meta.get('matchnum', ''))

print(f'Existing match dirs: {len(existing_dirs)}')

all_nums = {m['matchnum']: m for m in sat}
missing = {k: v for k, v in all_nums.items() if k not in existing_dirs}
print(f'Missing match dirs: {len(missing)}')
for k in sorted(missing.keys()):
    m = missing[k]
    print(f'  {k}: {m["home"]} vs {m["away"]} (fid={m["fid"]})')
