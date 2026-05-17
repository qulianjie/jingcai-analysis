import os, json
from datetime import datetime

dates = ['2026-05-07', '2026-05-08', '2026-05-09', '2026-05-10', '2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14']
results = []

for date in dates:
    data_dir = 'jingcai/tasks/%s/data' % date
    if os.path.isdir(data_dir):
        matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match')])
        total = len(matches)
        updated = 0
        pending = []
        
        for m in matches:
            step8 = os.path.join(data_dir, m, 'group03_asian', 'step8_same_league.txt')
            step19 = os.path.join(data_dir, m, 'group06_baijia', 'step19_baijia_compare.txt')
            
            s8_ok = os.path.exists(step8) and os.path.getsize(step8) > 100
            s19_ok = os.path.exists(step19) and os.path.getsize(step19) > 100
            
            if s8_ok and s19_ok:
                s8mod = datetime.fromtimestamp(os.path.getmtime(step8))
                if s8mod.date() >= datetime.now().date():
                    updated += 1
                else:
                    pending.append(m)
            else:
                pending.append(m)
        
        results.append('%s: %d total, %d updated, %d pending' % (date, total, updated, len(pending)))
        if pending:
            for p in pending[:5]:
                results.append('  %s' % p)
            if len(pending) > 5:
                results.append('  ... and %d more' % (len(pending)-5))

with open('jingcai/actual_status.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
