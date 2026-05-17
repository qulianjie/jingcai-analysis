import os, json

dates = ['2026-05-08', '2026-05-09', '2026-05-10', '2026-05-11', '2026-05-12']
results = []

for date in dates:
    data_dir = 'jingcai/tasks/%s/data' % date
    if os.path.isdir(data_dir):
        matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match')])
        results.append('%s: %d matches' % (date, len(matches)))
        
        # 检查之前说失败的match是否存在
        failed_nums = {'2026-05-08': ['match11'], '2026-05-09': ['match5', 'match7'], 
                      '2026-05-10': ['match1'], '2026-05-11': ['match6'],
                      '2026-05-12': ['match7', 'match17']}
        
        if date in failed_nums:
            for num in failed_nums[date]:
                full = os.path.join(data_dir, num)
                exists = os.path.isdir(full)
                results.append('  %s exists: %s' % (num, exists))
                if exists:
                    meta_path = os.path.join(full, 'meta.json')
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        results.append('    %s vs %s | %s | fid:%s' % (meta.get('home'), meta.get('away'), meta.get('league'), meta.get('fid')))

with open('jingcai/check_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
