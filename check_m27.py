import os

DATA_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'

# Find match27 dirs
for d in os.listdir(DATA_DIR):
    if d.startswith('match27'):
        dp = os.path.join(DATA_DIR, d)
        print(f'Dir: {d}')
        for f in os.listdir(dp):
            fp = os.path.join(dp, f)
            if os.path.isfile(fp):
                print(f'  {f}: {os.path.getsize(fp)}B')
            elif os.path.isdir(fp):
                for sf in os.listdir(fp):
                    sfp = os.path.join(fp, sf)
                    if os.path.isfile(sfp):
                        print(f'  {fp}/{sf}: {os.path.getsize(sfp)}B')
