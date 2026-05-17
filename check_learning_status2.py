# -*- coding: utf-8 -*-
import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

out = []
out.append('Generated at: ' + str(data.get('generated_at', '-')))
out.append('Total matches: ' + str(data.get('total_matches', '-')))
out.append('Total dates: ' + str(data.get('total_dates', '-')))
out.append('')

stats = data.get('_raw_combo_stats', {})
out.append('Combo label count: ' + str(len(stats)))

dims = {}
for key in stats:
    parts = key.split(':')
    if len(parts) == 2:
        dim = parts[0]
        dims[dim] = dims.get(dim, 0) + 1

out.append('')
out.append('Dimension labels:')
for d in sorted(dims.items(), key=lambda x: -x[1]):
    out.append('  %s: %d' % (d[0], d[1]))

out.append('')
high = data.get('high_accuracy_patterns', [])
out.append('High accuracy combos (>=60%%,>=5): %d' % len(high))
for p in high[:10]:
    out.append('  %s: %.0f%% (%d/%d)' % (p.get('combo',''), p.get('accuracy',0)*100, p.get('correct',0), p.get('total',0)))

out.append('')
low = data.get('low_accuracy_patterns', [])
out.append('Low accuracy combos (<=35%%,>=5): %d' % len(low))
for p in low[:5]:
    out.append('  %s: %.0f%% (%d/%d)' % (p.get('combo',''), p.get('accuracy',0)*100, p.get('correct',0), p.get('total',0)))

out.append('')
# Check if let_qiu trend exists
let_qiu_keys = [k for k in stats if k.startswith('\u8ba9\u7443')]
out.append('Let_qiu trend keys: %d' % len(let_qiu_keys))
for k in sorted(let_qiu_keys)[:10]:
    out.append('  %s' % k)

# Check 欧赔 trend keys
ou_pei_keys = [k for k in stats if k.startswith('\u6b27\u8d54')]
out.append('Oupie trend keys: %d' % len(ou_pei_keys))

# Check 百家 keys
bai_jia_keys = [k for k in stats if k.startswith('\u767e\u5bb6')]
out.append('Baijia trend keys: %d' % len(bai_jia_keys))

# Check ya_pan keys
ya_pan_keys = [k for k in stats if k.startswith('\u4e9a\u76d8')]
out.append('Yapan trend keys: %d' % len(ya_pan_keys))

result = '\n'.join(out)
with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\status_out.txt', 'w', encoding='utf-8') as f:
    f.write(result)
print(result)
