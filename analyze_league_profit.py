# -*- coding: utf-8 -*-
"""庄家盈亏方向 × 联赛 分组分析 (大样本)"""
import os, json

BASE = 'jingcai/tasks'

# 收集所有有step26的数据
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
        
        league = meta.get('league', '')
        if not league:
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
        if not any(v in ('赢钱', '亏钱') for v in profit_dir.values()):
            continue
        
        records.append({
            'date': d,
            'matchnum': meta.get('matchnum', ''),
            'match': meta.get('match', ''),
            'league': league,
            'profit_dir': profit_dir,
        })

print(f'有效记录: {len(records)}场')

# 按联赛分组
leagues = {}
for r in records:
    key = r['league']
    if key not in leagues:
        leagues[key] = []
    leagues[key].append(r)

print(f'共{len(leagues)}个联赛:')

# 排序: 按样本量降序
sorted_leagues = sorted(leagues.items(), key=lambda x: -len(x[1]))

print(f'\n{"="*90}')
print(f'{"联赛":20s} | {"场次":>4s} | {"胜(赢%":>9s} | {"平(赢%":>9s} | {"负(赢%":>9s} | 庄家偏好')
print(f'{"-"*90}')

for league, items in sorted_leagues:
    total = len(items)
    if total < 5:
        continue  # 样本太少跳过
    
    win_counts = {'胜': 0, '平': 0, '负': 0}
    total_valid = {'胜': 0, '平': 0, '负': 0}
    
    for item in items:
        for cat in ['胜', '平', '负']:
            d = item['profit_dir'].get(cat, '')
            if d in ('赢钱', '亏钱'):
                total_valid[cat] += 1
                if d == '赢钱':
                    win_counts[cat] += 1
    
    line = f'{league:<20s}'
    line += f' | {total:>4d}'
    
    prefs = []
    for cat in ['胜', '平', '负']:
        tv = total_valid[cat]
        if tv > 0:
            pct = win_counts[cat] / tv * 100
            line += f' | {win_counts[cat]}赢/{tv}场({pct:.0f}%)'
            if pct >= 65:
                prefs.append(f'{cat}向' if cat != '平' else '平向')
            elif pct <= 35:
                prefs.append(f'防{cat}')
        else:
            line += f' | -'
    
    pref_str = ', '.join(prefs) if prefs else '-'
    line += f' | {pref_str}'
    print(line)

print(f'\n{"="*90}')

# 关键发现
print(f'\n=== 关键发现 (样本≥5场，单向≥65%或≤35%) ===\n')

strong_signals = []
for league, items in sorted_leagues:
    total = len(items)
    if total < 5:
        continue
    
    win_counts = {'胜': 0, '平': 0, '负': 0}
    total_valid = {'胜': 0, '平': 0, '负': 0}
    
    for item in items:
        for cat in ['胜', '平', '负']:
            d = item['profit_dir'].get(cat, '')
            if d in ('赢钱', '亏钱'):
                total_valid[cat] += 1
                if d == '赢钱':
                    win_counts[cat] += 1
    
    for cat in ['胜', '平', '负']:
        tv = total_valid[cat]
        if tv < 5:
            continue
        pct = win_counts[cat] / tv * 100
        if pct >= 65:
            strong_signals.append(f'### {league} 方向:{cat} 庄家赢钱率{pct:.0f}%({win_counts[cat]}/{tv}场) -> 看好该方向')
        elif pct <= 35:
            strong_signals.append(f'### {league} 方向:{cat} 庄家亏钱率{(100-pct):.0f}%({tv-win_counts[cat]}/{tv}场) -> 利好该方向投注')

if strong_signals:
    for s in strong_signals:
        print(s)
else:
    print('当前数据量下未发现强信号')

# 保存JSON
output = {'total_records': len(records), 'leagues': {}}
for league, items in sorted_leagues:
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
    
    output['leagues'][league] = {
        'count': total,
        'win': {cat: win_counts[cat] for cat in ['胜', '平', '负']},
        'valid': {cat: total_valid[cat] for cat in ['胜', '平', '负']},
        'win_pct': {cat: round(win_counts[cat]/total_valid[cat]*100,1) if total_valid[cat]>0 else 0 for cat in ['胜', '平', '负']},
        'detail': [{'matchnum': r['matchnum'], 'match': r['match'], 'dir': r['profit_dir']} for r in items[:20]],
    }

out_path = 'jingcai/analysis_league_profit.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 保存可读文本
txt_path = 'jingcai/analysis_league_profit.txt'
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write('# 庄家盈亏方向 × 联赛 分组分析\n')
    f.write(f'# 数据量: {len(records)}场\n')
    f.write(f'# 日期范围: 2026-04-01 ~ 2026-05-09\n\n')
    
    f.write(f'{"联赛":20s} | {"场次":>4s} | {"胜(赢%":>9s} | {"平(赢%":>9s} | {"负(赢%":>9s} | 庄家偏好\n')
    f.write(f'{"-"*90}\n')
    
    for league, items in sorted_leagues:
        total = len(items)
        if total < 5:
            continue
        win_counts = {'胜': 0, '平': 0, '负': 0}
        total_valid = {'胜': 0, '平': 0, '负': 0}
        for item in items:
            for cat in ['胜', '平', '负']:
                d = item['profit_dir'].get(cat, '')
                if d in ('赢钱', '亏钱'):
                    total_valid[cat] += 1
                    if d == '赢钱':
                        win_counts[cat] += 1
        
        line = f'{league:<20s}'
        line += f' | {total:>4d}'
        prefs = []
        for cat in ['胜', '平', '负']:
            tv = total_valid[cat]
            if tv > 0:
                pct = win_counts[cat] / tv * 100
                line += f' | {win_counts[cat]}赢/{tv}场({pct:.0f}%)'
                if pct >= 65:
                    prefs.append(f'{cat}向' if cat != '平' else '平向')
                elif pct <= 35:
                    prefs.append(f'防{cat}')
            else:
                line += f' | -'
        pref_str = ', '.join(prefs) if prefs else '-'
        line += f' | {pref_str}'
        f.write(line + '\n')
    
    f.write(f'\n{"="*90}\n')
    f.write(f'\n## 关键发现\n\n')
    
    if strong_signals:
        for s in strong_signals:
            f.write(s + '\n')
    else:
        f.write('当前数据量下未发现强信号\n')

print(f'\n分析结果已保存: {out_path}')
print(f'可读报告已保存: {txt_path}')
