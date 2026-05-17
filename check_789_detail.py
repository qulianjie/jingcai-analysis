import os, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted([d for d in os.listdir(base) if d.startswith('match')])

for d in dirs:
    if d.startswith('match7_') or d.startswith('match8_') or d.startswith('match9_'):
        dp = os.path.join(base, d)
        meta_path = os.path.join(dp, 'meta.json')
        
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        
        # Check all group dirs
        groups = ['group01_europe', 'group02_handicap', 'group03_asian', 'group04_teamA', 'group05_teamB', 'group06_baijia']
        print(f"\n=== {d} (matchnum={meta.get('matchnum','?')}, league={meta.get('league','?')}) ===")
        for g in groups:
            gp = os.path.join(dp, g)
            if os.path.exists(gp):
                files = os.listdir(gp)
                for f in files:
                    fp = os.path.join(gp, f)
                    sz = os.path.getsize(fp) if os.path.isfile(fp) else 0
                    print(f"  {g}/{f}: {sz}B")
            else:
                print(f"  {g}: NOT EXISTS")
