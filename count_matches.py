import json, os, sys

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks'
total = 0
completed = 0
in_progress = 0

for d in sorted(os.listdir(base)):
    dp = os.path.join(base, d)
    if not os.path.isdir(dp):
        continue
    sub = [x for x in os.listdir(dp) if os.path.isdir(os.path.join(dp, x))]
    if not sub:
        continue
    dir_total = 0
    dir_completed = 0
    for m in sub:
        mp = os.path.join(dp, m)
        meta_path = os.path.join(mp, 'meta.json')
        if os.path.exists(meta_path):
            try:
                meta = json.load(open(meta_path, 'r', encoding='utf-8'))
                if meta.get('status') == 'completed':
                    completed += 1
                    dir_completed += 1
                else:
                    in_progress += 1
            except:
                in_progress += 1
        else:
            in_progress += 1
        dir_total += 1
        total += 1
    print(f"{d}: {dir_completed}/{dir_total} completed")

print(f"\nTOTAL: {completed}/{total} completed, {in_progress} in progress")
