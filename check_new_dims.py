import json

data = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', encoding='utf-8'))
combos = data.get('_raw_combo_stats', {})
print(f'Total combos: {len(combos)}')

new_dims = [k for k in combos.keys() if '盈亏方向' in k or '投注占比' in k or '盈亏占比' in k]
if new_dims:
    print('New dimensions found:')
    for k in new_dims[:10]:
        v = combos[k]
        print(f'  {k}: {v.get("correct", 0)}/{v.get("total", 0)}')
else:
    print('No new dimensions found')
    print('First 5 combos:')
    for i, k in enumerate(list(combos.keys())[:5]):
        print(f'  {k}')
