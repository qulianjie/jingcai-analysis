import os, json

dates = ['2026-05-08', '2026-05-09', '2026-05-10', '2026-05-11', '2026-05-12']
results = []

for date in dates:
    data_dir = 'jingcai/tasks/%s/data' % date
    if os.path.isdir(data_dir):
        matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match')])
        results.append('%s: %d matches' % (date, len(matches)))
        
        # 显示前3个match目录名
        for m in matches[:3]:
            results.append('  %s' % m)
        if len(matches) > 3:
            results.append('  ... and %d more' % (len(matches)-3))

with open('jingcai/check_results2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
