# -*- coding: utf-8 -*-
"""澳门亚盘(即时盘) × 庄家盈亏方向(赢钱/亏钱) 分组分析"""
import os, json

BASE = 'jingcai/tasks'

# 收集所有有macau_line+step26的数据
records = []
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    for m in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, m)
        if not (os.path.isdir(mp) and m.startswith('match')):
            continue
        
        meta_path = os.path.join(mp, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        
        macau = meta.get('macau_line', '')
        if not macau:
            continue
        
        s26_path = os.path.join(mp, 'step26_profit_ratio.json')
        if not (os.path.exists(s26_path) and os.path.getsize(s26_path) > 0):
            continue
        
        s26 = json.load(open(s26_path, 'r', encoding='utf-8'))
        analysis = s26.get('analysis', {})
        if not analysis:
            continue
        
        profit_dir = {
            '胜': analysis.get('庄家胜盈亏', ''),
            '平': analysis.get('庄家平盈亏', ''),
            '负': analysis.get('庄家负盈亏', ''),
        }
        if not any(v for v in profit_dir.values()):
            continue
        
        records.append({
            'date': d,
            'matchnum': meta.get('matchnum', ''),
            'match': meta.get('match', ''),
            'league': meta.get('league', ''),
            'macau_line': macau,
            'profit_dir': profit_dir,
        })

print(f'有效记录: {len(records)}场 (有macau_line即时盘 + step26赢/亏方向)')

# 按macau_line分组
groups = {}
for r in records:
    key = r['macau_line']
    if key not in groups:
        groups[key] = []
    groups[key].append(r)

print(f'共{len(groups)}种亚盘:')

# 排序: 先主盘再受盘
def pan_sort_key(k):
    order = {'平手':0, '平手降':1, '平手升':2, '平手/半球':3, '平手/半球降':4, '平手/半球升':5,
             '半球':6, '半球/一球':7, '一球':8, '一球/球半':9, '球半':10, '两球':11,
             '受平手/半球':12, '受平手/半球降':13, '受半球':14, '受半球/一球':15,
             '受一球':16, '受一球/球半':17, '受球半':18}
    clean = k.replace(' ', '').replace('升','').replace('降','')
    priority = 0
    modifier = 0
    if '降' in k: modifier = 1
    elif '升' in k: modifier = 2
    base_key = k.replace(' ', '')
    if '升' in base_key: base_key = base_key.replace('升','')
    if '降' in base_key: base_key = base_key.replace('降','')
    for name, idx in order.items():
        if base_key == name.replace(' ', '').replace('降','').replace('升',''):
            return (idx, modifier)
    return (99, 0)

print(f'\n{"="*80}')
print(f'{"澳门亚盘(即时)":25s} | {"场次":>4s} | {"胜(赢%)":>9s} | {"平(赢%)":>9s} | {"负(赢%)":>9s} | 庄家偏好')
print(f'{"-"*80}')

for pan in sorted(groups.keys(), key=pan_sort_key):
    items = groups[pan]
    total = len(items)
    
    win_counts = {'胜': 0, '平': 0, '负': 0}
    total_valid = {'胜': 0, '平': 0, '负': 0}
    
    for item in items:
        for cat in ['胜', '平', '负']:
            d = item['profit_dir'].get(cat, '')
            if d in ('赢钱', '亏钱'):
                total_valid[cat] += 1
                if d == '赢钱':
                    win_counts[cat] += 1
    
    pad_len = max(6, len(pan))
    
    line = f'{pan:<25s}'
    line += f' | {total:>4d}'
    
    prefs = []
    for cat in ['胜', '平', '负']:
        tv = total_valid[cat]
        if tv > 0:
            pct = win_counts[cat] / tv * 100
            line += f' | {win_counts[cat]}赢/{tv}场({pct:.0f}%)'
            if pct >= 60:
                prefs.append(f'{cat}向' if cat != '平' else '平向')
            elif pct <= 40:
                prefs.append(f'防{cat}')
        else:
            line += f' | -'
    
    pref_str = ', '.join(prefs) if prefs else '-'
    line += f' | {pref_str}'
    print(line)

print(f'\n{"="*80}')

# 详细统计
print(f'\n=== 详细分组数据 ===\n')
for pan in sorted(groups.keys(), key=pan_sort_key):
    items = groups[pan]
    total = len(items)
    if total < 3:
        continue  # 样本太少跳过详细展示
    
    win_counts = {'胜': 0, '平': 0, '负': 0}
    total_valid = {'胜': 0, '平': 0, '负': 0}
    
    for item in items:
        for cat in ['胜', '平', '负']:
            d = item['profit_dir'].get(cat, '')
            if d in ('赢钱', '亏钱'):
                total_valid[cat] += 1
                if d == '赢钱':
                    win_counts[cat] += 1
    
    print(f'--- {pan} ({total}场) ---')
    for cat in ['胜', '平', '负']:
        tv = total_valid[cat]
        if tv > 0:
            pct = win_counts[cat] / tv * 100
            label = '庄家赢' if pct >= 60 else ('庄家亏' if pct <= 40 else '均衡')
            print(f'  {cat}: {win_counts[cat]}场赢钱/{tv}场有数据 ({pct:.0f}%) -> {label}')
        else:
            print(f'  {cat}: 无数据')
    print()

# 保存JSON
output = {'total_records': len(records), 'groups': {}}
for pan in sorted(groups.keys(), key=pan_sort_key):
    items = groups[pan]
    total = len(items)
    win_counts = {'胜': 0, '平': 0, '负': 0}
    total_valid = {'胜': 0, '平': 0, '负': 0}
    
    for item in items:
        for cat in ['胜', '平', '负']:
            d = item['profit_dir'].get(cat, '')
            if d in ('赢钱', '亏钱'):
                total_valid[cat] += 1
                if d == '赢钱':
                    win_counts[cat] += 1
    
    output['groups'][pan] = {
        'count': total,
        'win': {cat: win_counts[cat] for cat in ['胜', '平', '负']},
        'valid': {cat: total_valid[cat] for cat in ['胜', '平', '负']},
        'win_pct': {cat: round(win_counts[cat]/total_valid[cat]*100,1) if total_valid[cat]>0 else 0 for cat in ['胜', '平', '负']},
        'detail': [{'matchnum': r['matchnum'], 'league': r['league'], 'match': r['match'], 'dir': r['profit_dir']} for r in items],
    }

out_path = 'jingcai/analysis_macau_profit_v2.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n分析结果已保存: {out_path}')

# 保存可读文本报告
txt_path = 'jingcai/analysis_macau_profit_v2.txt'
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write('# 澳门亚盘(即时盘) × 庄家盈亏方向 分组分析\n')
    f.write(f'# 数据量: {len(records)}场\n')
    f.write(f'# 日期范围: 2026-04-01 ~ 2026-05-09\n\n')
    
    # 重新生成表格
    f.write(f'{"澳门亚盘(即时)":25s} | {"场次":>4s} | {"胜(赢%":>9s} | {"平(赢%":>9s} | {"负(赢%":>9s} | 庄家偏好\n')
    f.write(f'{"-"*80}\n')
    
    for pan in sorted(groups.keys(), key=pan_sort_key):
        items = groups[pan]
        total = len(items)
        win_counts = {'胜': 0, '平': 0, '负': 0}
        total_valid = {'胜': 0, '平': 0, '负': 0}
        for item in items:
            for cat in ['胜', '平', '负']:
                d = item['profit_dir'].get(cat, '')
                if d in ('赢钱', '亏钱'):
                    total_valid[cat] += 1
                    if d == '赢钱':
                        win_counts[cat] += 1
        
        line = f'{pan:<25s}'
        line += f' | {total:>4d}'
        prefs = []
        for cat in ['胜', '平', '负']:
            tv = total_valid[cat]
            if tv > 0:
                pct = win_counts[cat] / tv * 100
                line += f' | {win_counts[cat]}赢/{tv}场({pct:.0f}%)'
                if pct >= 60:
                    prefs.append(f'{cat}向')
                elif pct <= 40:
                    prefs.append(f'防{cat}')
            else:
                line += f' | -'
        pref_str = ', '.join(prefs) if prefs else '-'
        line += f' | {pref_str}'
        f.write(line + '\n')
    
    f.write(f'\n{"="*80}\n')
    f.write(f'\n## 关键发现\n\n')
    
    # 找庄家明显偏向的盘口
    strong_signals = []
    for pan in sorted(groups.keys(), key=pan_sort_key):
        g = output['groups'][pan]
        if g['count'] < 5:
            continue
        for cat in ['胜', '平', '负']:
            pct = g['win_pct'][cat]
            valid = g['valid'][cat]
            if valid >= 5 and pct >= 70:
                strong_signals.append(f'### {pan} 方向:{cat} 庄家赢钱率{pct}%({g["win"][cat]}/{valid}场)')
            elif valid >= 5 and pct <= 30:
                strong_signals.append(f'### {pan} 方向:{cat} 庄家亏钱率{(100-pct):.0f}%({valid-g["win"][cat]}/{valid}场) -> 利好该方向')
    
    if strong_signals:
        f.write('### 庄家明显偏向的信号 (样本≥5场，单向≥70%)\n\n')
        for s in strong_signals:
            f.write(s + '\n')
    else:
        f.write('当前数据量下未发现强信号，建议继续积累更多样本\n')

print(f'可读报告已保存: {txt_path}')
