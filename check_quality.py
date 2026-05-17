# -*- coding: utf-8 -*-
"""
检查 step8 和 step19 数据的实际有效性（使用正确的阈值）
step8 阈值: >1269 bytes（空模板大小）
step19 阈值: >1738 bytes（空模板大小）
"""
import os, json

dates = ['2026-05-07', '2026-05-08', '2026-05-09', '2026-05-10', 
         '2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14']

S8_THRESHOLD = 1269
S19_THRESHOLD = 1738

results = []
total = 0
s8_ok = 0
s8_fail = 0
s19_ok = 0
s19_fail = 0
all_s19_fail = []

for date in dates:
    data_dir = 'jingcai/tasks/%s/data' % date
    if not os.path.isdir(data_dir):
        continue
    
    matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match')])
    date_total = len(matches)
    date_s8_ok = 0
    date_s8_fail = 0
    date_s19_ok = 0
    date_s19_fail = 0
    s8_fail_matches = []
    s19_fail_matches = []
    
    for m in matches:
        base = os.path.join(data_dir, m)
        
        # 检查 step8
        step8 = os.path.join(base, 'group03_asian', 'step8_same_league.txt')
        if os.path.exists(step8):
            size = os.path.getsize(step8)
            if size > S8_THRESHOLD:
                date_s8_ok += 1
            else:
                date_s8_fail += 1
                s8_fail_matches.append('%s(%d)' % (m, size))
        else:
            date_s8_fail += 1
            s8_fail_matches.append('%s(MISSING)' % m)
        
        # 检查 step19
        step19 = os.path.join(base, 'group06_baijia', 'step19_baijia_compare.txt')
        if os.path.exists(step19):
            size = os.path.getsize(step19)
            if size > S19_THRESHOLD:
                date_s19_ok += 1
            else:
                date_s19_fail += 1
                s19_fail_matches.append('%s(%d)' % (m, size))
                all_s19_fail.append('%s/%s' % (date, m))
        else:
            date_s19_fail += 1
            s19_fail_matches.append('%s(MISSING)' % m)
            all_s19_fail.append('%s/%s' % (date, m))
    
    total += date_total
    s8_ok += date_s8_ok
    s8_fail += date_s8_fail
    s19_ok += date_s19_ok
    s19_fail += date_s19_fail
    
    line = '%s: %d total | step8: %d ok, %d fail | step19: %d ok, %d fail' % (
        date, date_total, date_s8_ok, date_s8_fail, date_s19_ok, date_s19_fail
    )
    results.append(line)
    
    if s8_fail_matches:
        results.append('  step8 fail: ' + ', '.join(s8_fail_matches[:5]))
    if s19_fail_matches:
        results.append('  step19 fail: ' + ', '.join(s19_fail_matches[:5]))

results.append('')
results.append('TOTAL: %d matches | step8: %d ok, %d fail | step19: %d ok, %d fail' % (
    total, s8_ok, s8_fail, s19_ok, s19_fail
))
results.append('')
results.append('step19 空数据比赛 (%d场):' % len(all_s19_fail))
for f in all_s19_fail:
    results.append('  ' + f)

with open('jingcai/quality_check_v2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/quality_check_v2.txt')
