# -*- coding: utf-8 -*-
import os, glob
data_dir = 'jingcai/tasks/2026-05-09/data'
dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
print(f'Total match dirs: {len(dirs)}')
for d in dirs:
    meta_path = os.path.join(data_dir, d, 'meta.json')
    groups_path = os.path.join(data_dir, d, 'group01_europe')
    if os.path.exists(meta_path):
        import json
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        mn = meta.get('matchnum', '?')
    else:
        mn = '?'
    # count files
    all_files = []
    for root, dirs_list, files in os.walk(os.path.join(data_dir, d)):
        all_files.extend(files)
    print(f'  {d}: matchnum={mn}, {len(all_files)} files')
