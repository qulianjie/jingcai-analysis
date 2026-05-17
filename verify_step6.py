import os

DATA_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-12/data'
count = 0
asian_count = 0
macau_count = 0
for d in sorted(os.listdir(DATA_DIR)):
    dp = os.path.join(DATA_DIR, d)
    if not os.path.isdir(dp):
        continue
    s6 = os.path.join(dp, 'group03_asian', 'step6_asian_base.txt')
    if os.path.exists(s6):
        count += 1
        content = open(s6, 'r', encoding='utf-8').read()
        is_asian = '亚盘' in content
        has_macau = '澳门' in content
        if is_asian:
            asian_count += 1
        if has_macau:
            macau_count += 1
        if not is_asian:
            print('ERROR: %s is not asian' % d)
print('Total: %d, Asian: %d, Macau: %d' % (count, asian_count, macau_count))
