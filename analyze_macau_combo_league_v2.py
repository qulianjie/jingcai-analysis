# -*- coding: utf-8 -*-
"""
澳门即时盘 × 盈亏方向组合 → 分组统计 (不依赖实际比分)
按联赛分组输出

盈亏方向: True=庄家赚钱(冷门), False=庄家亏钱(大热)
盈亏组合: 胜X平X负X (赢=庄家赚, 亏=庄家亏)
"""
import os, json
from collections import defaultdict

BASE = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# 收集数据
records = []
total = 0
missing_macau = 0
missing_s26 = 0

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    for m_name in sorted(os.listdir(data_dir)):
        m_path = os.path.join(data_dir, m_name)
        if not (os.path.isdir(m_path) and m_name.startswith('match')):
            continue
        
        meta_path = os.path.join(m_path, 'meta.json')
        s26_path = os.path.join(m_path, 'step26_profit_ratio.json')
        if not (os.path.exists(meta_path) and os.path.exists(s26_path)):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        s26 = json.load(open(s26_path, 'r', encoding='utf-8'))
        
        total += 1
        macau_line = meta.get('macau_line', '')
        if not macau_line:
            missing_macau += 1
            continue
        
        league = meta.get('league', '')
        
        # 提取盈亏组合
        p = s26.get('profit_data', {})
        win_dir = p.get('主胜', {}).get('profit_dir', None)
        draw_dir = p.get('平局', {}).get('profit_dir', None)
        lose_dir = p.get('客胜', {}).get('profit_dir', None)
        
        if win_dir is None or draw_dir is None or lose_dir is None:
            missing_s26 += 1
            continue
        
        win_label = '赢' if win_dir else '亏'
        draw_label = '赢' if draw_dir else '亏'
        lose_label = '赢' if lose_dir else '亏'
        combo = f'胜{win_label}平{draw_label}负{lose_label}'
        
        records.append({
            'macau': macau_line,
            'league': league,
            'combo': combo,
            'matchnum': meta.get('matchnum', ''),
            'home': meta.get('home', ''),
            'away': meta.get('away', ''),
        })

print(f'数据: {len(records)}场 (总{total}, 缺macau:{missing_macau}, 缺s26:{missing_s26})')

# ========== 分析1: macau_line × 盈亏组合 ==========
print('\n' + '='*120)
print('澳门即时盘 × 盈亏方向组合 分组统计')
print('='*120)

macau_combo = defaultdict(int)
for r in records:
    key = (r['macau'], r['combo'])
    macau_combo[key] += 1

# 按盘口分组
macau_groups = defaultdict(list)
for (macau, combo), count in macau_combo.items():
    macau_groups[macau].append((combo, count))

# 定义盘口顺序
macau_order = [
    '平手', '平手 降', '平手 升',
    '平手/半球', '平手/半球 降', '平手/半球 升',
    '半球', '半球 升',
    '半球/一球', '半球/一球 降', '半球/一球 升',
    '一球', '一球 升',
    '一球/球半', '一球/球半 升',
    '球半', '球半 降',
    '两球',
    '受平手/半球', '受平手/半球 降', '受平手/半球 升',
    '受半球', '受半球/一球',
    '受一球', '受一球/球半',
    '受球半', '受两球',
    '球半/两球', '球半/两球 降', '球半/两球 升',
]

print(f'\n{"盘口":<18} | {"盈亏组合":<16} | {"场次":>4} | 含义')
print('-'*120)

def combo_meaning(combo, count):
    """解读盈亏组合"""
    parts = []
    if '胜赢' in combo: parts.append('庄家看好主胜')
    elif '胜亏' in combo: parts.append('庄家防主胜(大热)')
    if '平赢' in combo: parts.append('庄家看好平')
    elif '平亏' in combo: parts.append('庄家防平(大热)')
    if '负赢' in combo: parts.append('庄家看好客胜')
    elif '负亏' in combo: parts.append('庄家防客胜(大热)')
    return ' + '.join(parts)

for macau in macau_order:
    if macau not in macau_groups:
        continue
    items = macau_groups[macau]
    # 按场次排序
    items.sort(key=lambda x: x[1], reverse=True)
    
    total_count = sum(c for _, c in items)
    
    for i, (combo, count) in enumerate(items):
        pct = count / total_count * 100
        meaning = combo_meaning(combo, count)
        
        if i == 0:
            print(f'{macau:<18} | {combo:<16} | {count:>4} ({pct:.0f}%) | {meaning}')
        else:
            print(f'{"":<18} | {combo:<16} | {count:>4} ({pct:.0f}%) | {meaning}')

# ========== 分析2: 联赛 × 盈亏组合 ==========
print('\n' + '\n' + '='*120)
print('联赛 × 盈亏方向组合 分组统计 (样本≥3)')
print('='*120)

league_combo = defaultdict(lambda: defaultdict(int))
for r in records:
    league_combo[r['league']][r['combo']] += 1

# 按总场次排序联赛
league_totals = {league: sum(combos.values()) for league, combos in league_combo.items()}
sorted_leagues = sorted(league_totals.keys(), key=lambda x: league_totals[x], reverse=True)

print(f'\n{"联赛":<12} | {"盈亏组合":<16} | {"场次":>4} | 占比 | 含义')
print('-'*120)

for league in sorted_leagues:
    combos = league_combo[league]
    total_count = sum(combos.values())
    
    if total_count < 3:
        continue
    
    # 按场次排序
    sorted_combos = sorted(combos.items(), key=lambda x: x[1], reverse=True)
    
    for i, (combo, count) in enumerate(sorted_combos):
        pct = count / total_count * 100
        meaning = combo_meaning(combo, count)
        
        if i == 0:
            print(f'{league:<12} | {combo:<16} | {count:>4} | {pct:>5.0f}% | {meaning}')
        else:
            print(f'{"":<12} | {combo:<16} | {count:>4} | {pct:>5.0f}% | {meaning}')

# ========== 分析3: 盘口 × 联赛 × 盈亏组合 (三维度) ==========
print('\n' + '\n' + '='*120)
print('盘口 × 联赛 × 盈亏组合 (样本≥2)')
print('='*120)

tri = defaultdict(int)
for r in records:
    key = (r['macau'], r['league'], r['combo'])
    tri[key] += 1

# 过滤≥2
tri_filtered = {k: v for k, v in tri.items() if v >= 2}

# 按盘口分组
tri_by_macau = defaultdict(list)
for (macau, league, combo), count in tri_filtered.items():
    tri_by_macau[macau].append((league, combo, count))

print(f'\n{"盘口":<18} | {"联赛":<12} | {"盈亏组合":<16} | {"场次":>4} | 含义')
print('-'*120)

for macau in macau_order:
    if macau not in tri_by_macau:
        continue
    items = tri_by_macau[macau]
    items.sort(key=lambda x: x[2], reverse=True)
    
    for league, combo, count in items:
        meaning = combo_meaning(combo, count)
        print(f'{macau:<18} | {league:<12} | {combo:<16} | {count:>4} | {meaning}')

# ========== 分析4: 盈亏方向统计 ==========
print('\n' + '\n' + '='*120)
print('庄家盈亏方向汇总 (173场)')
print('='*120)

dir_stats = {'主胜': {'赚': 0, '亏': 0}, '平局': {'赚': 0, '亏': 0}, '客胜': {'赚': 0, '亏': 0}}
for r in records:
    combo = r['combo']
    if '胜赢' in combo: dir_stats['主胜']['赚'] += 1
    elif '胜亏' in combo: dir_stats['主胜']['亏'] += 1
    if '平赢' in combo: dir_stats['平局']['赚'] += 1
    elif '平亏' in combo: dir_stats['平局']['亏'] += 1
    if '负赢' in combo: dir_stats['客胜']['赚'] += 1
    elif '负亏' in combo: dir_stats['客胜']['亏'] += 1

print(f'\n{"方向":<8} | {"庄家赚(冷门)":>10} | {"庄家亏(大热)":>10} | 庄家偏好')
print('-'*60)

for dir_name in ['主胜', '平局', '客胜']:
    s = dir_stats[dir_name]
    total_d = s['赚'] + s['亏']
    if total_d == 0:
        continue
    win_pct = s['赚'] / total_d * 100
    lose_pct = s['亏'] / total_d * 100
    
    if win_pct > lose_pct:
        pref = f'庄家偏好{dir_name}(赚{win_pct:.0f}%)'
    elif lose_pct > win_pct:
        pref = f'{dir_name}大热(亏{lose_pct:.0f}%)'
    else:
        pref = '均衡'
    
    print(f'{dir_name:<8} | {s["赚"]:>10}({win_pct:.0f}%) | {s["亏"]:>10}({lose_pct:.0f}%) | {pref}')

# ========== 保存 ==========
output = {
    '元信息': {'总场次': total, '有效场次': len(records), '缺macau_line': missing_macau, '缺s26': missing_s26},
    '盘口_盈亏组合': {f'{k[0]}|{k[1]}': v for k, v in macau_combo.items()},
    '联赛_盈亏组合': {f'{k[0]}|{k[1]}': v for league, combos in league_combo.items() for k, v in combos.items()},
    '三维度_盘口_联赛_组合': {f'{k[0]}|{k[1]}|{k[2]}': v for k, v in tri_filtered.items()},
    '盈亏方向汇总': dir_stats,
}

out_file = r'C:\Users\lianjie\.openclaw\workspace\jingcai\analysis_macau_combo_league.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n完整JSON已保存: {out_file}')
