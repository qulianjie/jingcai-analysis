# -*- coding: utf-8 -*-
"""
澳门即时盘 × 盈亏方向 × 联赛 三维交叉分析（带实际比分）
"""
import os, json, re
from collections import defaultdict

BASE = os.path.join('jingcai', 'tasks')

# 收集所有数据
records = []
total = 0
score_count = 0

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
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
            continue
        
        league = meta.get('league', '')
        
        # 获取实际胜平负
        actual = None
        score = meta.get('score', '')
        if score and ':' in score:
            try:
                parts = score.split(':')
                home, away = int(parts[0]), int(parts[1])
                if home > away:
                    actual = '胜'
                elif home == away:
                    actual = '平'
                else:
                    actual = '负'
                score_count += 1
            except:
                pass
        
        # 提取盈亏组合
        p = s26.get('profit_data', {})
        win_dir = p.get('主胜', {}).get('profit_dir', None)
        draw_dir = p.get('平局', {}).get('profit_dir', None)
        lose_dir = p.get('客胜', {}).get('profit_dir', None)
        
        if win_dir is None:
            continue
        
        win_label = '赢' if win_dir else '亏'
        draw_label = '赢' if draw_dir else '亏'
        lose_label = '赢' if lose_dir else '亏'
        combo = f'胜{win_label}平{draw_label}负{lose_label}'
        
        records.append({
            'macau': macau_line,
            'league': league,
            'combo': combo,
            'actual': actual,
            'matchnum': meta.get('matchnum', ''),
            'home': meta.get('home', ''),
            'away': meta.get('away', ''),
        })

print(f'数据: {len(records)}场 (有比分: {score_count})')

# ========== 分析1: 盘口 × 盈亏组合 → 胜平负概率 ==========
print('\n' + '='*140)
print('澳门即时盘 × 盈亏方向组合 → 胜平负概率')
print('='*140)

combo_groups = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in records:
    if r['actual']:  # 只统计有比分的
        key = (r['macau'], r['combo'])
        combo_groups[key]['count'] += 1
        combo_groups[key][r['actual']] += 1

# 筛选样本≥3
print(f'\n{"盘口":<18} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>6} | {"平(%)":>6} | {"负(%)":>6} | 最大概率')
print('-'*140)

macau_order = ['平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半', '球半',
               '受平手/半球', '受半球', '受半球/一球', '受一球', '受一球/球半', '受球半']

current_macau = None
found = False
for macau in macau_order:
    for (m, c), v in sorted(combo_groups.items()):
        if m != macau or v['count'] < 3:
            continue
        found = True
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        sig = []
        if win_pct >= 70: sig.append('胜↑')
        if lose_pct >= 70: sig.append('负↑')
        if draw_pct <= 15: sig.append('平↓')
        sig_str = ','.join(sig) if sig else ''
        
        prefix = macau if current_macau != macau else ''
        current_macau = macau
        
        print(f'{prefix:<18} | {c:<16} | {v["count"]:>4} | {win_pct:>5.1f}% | {draw_pct:>5.1f}% | {lose_pct:>5.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

if not found:
    print('（样本≥3的组合不足，显示所有组合）')
    for (m, c), v in sorted(combo_groups.items()):
        if v['count'] < 1:
            continue
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        sig = []
        if win_pct >= 70: sig.append('胜↑')
        if lose_pct >= 70: sig.append('负↑')
        if draw_pct <= 15: sig.append('平↓')
        sig_str = ','.join(sig) if sig else ''
        
        print(f'{m:<18} | {c:<16} | {v["count"]:>4} | {win_pct:>5.1f}% | {draw_pct:>5.1f}% | {lose_pct:>5.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# ========== 分析2: 联赛 × 盈亏组合 → 胜平负概率 ==========
print('\n' + '\n' + '='*140)
print('联赛 × 盈亏组合 → 胜平负概率')
print('='*140)

league_combo = defaultdict(lambda: defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0}))
for r in records:
    if r['actual']:
        league_combo[r['league']][r['combo']]['count'] += 1
        league_combo[r['league']][r['combo']][r['actual']] += 1

print(f'\n{"联赛":<12} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>6} | {"平(%)":>6} | {"负(%)":>6} | 最大概率')
print('-'*140)

league_totals = {league: sum(c.values()) for combos in league_combo.values() for c in combos.values()}
sorted_leagues = sorted(league_totals.keys(), key=lambda x: league_totals[x], reverse=True)

for league in sorted_leagues[:10]:
    combos = league_combo[league]
    sorted_combos = sorted(combos.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for combo, v in sorted_combos:
        if v['count'] < 1:
            continue
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        sig = []
        if win_pct >= 70: sig.append('胜↑')
        if lose_pct >= 70: sig.append('负↑')
        if draw_pct <= 15: sig.append('平↓')
        sig_str = ','.join(sig) if sig else ''
        
        print(f'{league:<12} | {combo:<16} | {v["count"]:>4} | {win_pct:>5.1f}% | {draw_pct:>5.1f}% | {lose_pct:>5.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# ========== 分析3: 三维度（盘口 × 联赛 × 盈亏组合） ==========
print('\n' + '\n' + '='*140)
print('盘口 × 联赛 × 盈亏组合（三维度）')
print('='*140)

tri = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in records:
    if r['actual']:
        key = (r['macau'], r['league'], r['combo'])
        tri[key]['count'] += 1
        tri[key][r['actual']] += 1

print(f'\n{"盘口":<18} | {"联赛":<12} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>6} | {"平(%)":>6} | {"负(%)":>6} | 最大概率')
print('-'*140)

tri_sorted = sorted(tri.items(), key=lambda x: x[1]['count'], reverse=True)

for (macau, league, combo), v in tri_sorted[:30]:
    if v['count'] < 1:
        continue
    win_pct = v['胜'] / v['count'] * 100
    draw_pct = v['平'] / v['count'] * 100
    lose_pct = v['负'] / v['count'] * 100
    
    probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
    max_dir, max_pct = max(probs, key=lambda x: x[1])
    
    sig = []
    if win_pct >= 70: sig.append('胜↑')
    if lose_pct >= 70: sig.append('负↑')
    if draw_pct <= 15: sig.append('平↓')
    sig_str = ','.join(sig) if sig else ''
    
    print(f'{macau:<18} | {league:<12} | {combo:<16} | {v["count"]:>4} | {win_pct:>5.1f}% | {draw_pct:>5.1f}% | {lose_pct:>5.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# ========== 分析4: 盈亏方向汇总（所有166场） ==========
print('\n' + '\n' + '='*140)
print('庄家盈亏方向汇总（166场）')
print('='*140)

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

# ========== 保存JSON ==========
output = {
    '元信息': {'总场次': total, '有效场次': len(records), '有比分': score_count, '无比分': total - score_count},
    '盘口_盈亏组合_胜平负': {f'{k[0]}|{k[1]}': v for k, v in combo_groups.items()},
    '联赛_盈亏组合_胜平负': {f'{k[0]}|{k[1]}': v for league, combos in league_combo.items() for k, v in combos.items()},
    '三维度_盘口_联赛_组合_胜平负': {f'{k[0]}|{k[1]}|{k[2]}': v for k, v in tri.items()},
    '盈亏方向汇总': dir_stats,
}

out_file = os.path.join('jingcai', 'analysis_macau_combo_league_with_scores.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n完整JSON已保存: {out_file}')
