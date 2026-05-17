import os, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted(os.listdir(base))
print(f'Total match dirs: {len(dirs)}')

files_to_check = {
    'step8': 'step8_same_league.txt',
    'step9': 'step9_home_history.txt',
    'step14': 'step14_away_history.txt',
    'step19': 'step19_baijia_compare.txt',
}

results = {k: {'missing': 0, 'empty': 0, 'has_data': 0, 'sizes': []} for k in files_to_check}

for d in dirs:
    dp = os.path.join(base, d)
    if not os.path.isdir(dp):
        continue
    for key, fname in files_to_check.items():
        fp = os.path.join(dp, fname)
        if not os.path.exists(fp):
            results[key]['missing'] += 1
        else:
            sz = os.path.getsize(fp)
            results[key]['sizes'].append(sz)
            if sz <= 50:
                results[key]['empty'] += 1
            else:
                results[key]['has_data'] += 1

for key, r in results.items():
    sizes = sorted(r['sizes']) if r['sizes'] else []
    print(f"\n{key}: missing={r['missing']}, empty(<=50B)={r['empty']}, has_data={r['has_data']}")
    if sizes:
        print(f"  sizes: {sizes[:5]}...{sizes[-5:]}")
        print(f"  min={sizes[0]}, max={sizes[-1]}, median={sizes[len(sizes)//2]}")

# Check empty template sizes
print("\n--- Checking empty template content ---")
for key, fname in files_to_check.items():
    # Find first file with data
    for d in dirs:
        dp = os.path.join(base, d)
        fp = os.path.join(dp, fname)
        if os.path.exists(fp) and os.path.getsize(fp) > 50:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            print(f"\n{fname} (from {d}, {os.path.getsize(fp)}B):")
            # Find empty template pattern
            lines = content.strip().split('\n')
            for line in lines[:5]:
                print(f"  {line[:100]}")
            break
