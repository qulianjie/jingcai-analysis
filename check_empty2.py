import os, re, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16'

# Get all match directories
data_dir = os.path.join(base, 'data')
data_dirs = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
print(f"Match dirs in data/: {len(data_dirs)}")

# Get all .md reports (excluding sunday_matches.md)
md_files = sorted([f for f in os.listdir(base) if f.endswith('.md') and f != 'sunday_matches.md'])
print(f"Report .md files: {len(md_files)}")

# Extract match numbers from reports
report_nums = set()
for f in md_files:
    m = re.search(r'(\d{3})_', f)
    if m:
        report_nums.add(m.group(1))
print(f"Report numbers: {sorted(report_nums)}")

# Get expected numbers from match dirs
dir_nums = set()
for d in data_dirs:
    m = re.search(r'match(\d+)', d)
    if m:
        dir_nums.add(f"{int(m.group(1)):03d}")
print(f"Dir numbers: {sorted(dir_nums)}")

# Missing reports
missing = sorted(dir_nums - report_nums)
extra = sorted(report_nums - dir_nums)
if missing:
    print(f"Missing reports for dirs: {missing}")
if extra:
    print(f"Extra reports without dirs: {extra}")

# Check which files exist vs don't in each match dir
print("\n--- File presence check ---")
target_files = ['step8_same_league.txt', 'step9_home_history.txt', 
                'step14_away_history.txt', 'step19_baijia_compare.txt']
for d in data_dirs[:5]:
    dp = os.path.join(data_dir, d)
    print(f"\n{d}:")
    for f in os.listdir(dp):
        fp = os.path.join(dp, f)
        if os.path.isfile(fp):
            print(f"  {f}: {os.path.getsize(fp)}B")
