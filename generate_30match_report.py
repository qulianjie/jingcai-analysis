# -*- coding: utf-8 -*-
"""
基于30场（2026-05-09）数据生成分析报告
"""
import os, json

BASE = os.path.join('jingcai', 'tasks', '2026-05-09', 'data')

matches = []
for m in sorted(os.listdir(BASE)):
    if not m.startswith('match'):
        continue
    
    meta_path = os.path.join(BASE, m, 'meta.json')
    s26_path = os.path.join(BASE, m, 'step26_profit_ratio.json')
    
    if not (os.path.exists(meta_path) and os.path.exists(s26_path)):
        continue
    
    meta = json.load(open(meta_path, 'r', encoding='utf-8'))
    s26 = json.load(open(s26_path, 'r', encoding='utf-8'))
    
    macau = meta.get('macau_line', '')
    league = meta.get('league', '')
    matchnum = meta.get('matchnum', '')
    home = meta.get('home', '')
    away = meta.get('away', '')
    
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
    
    # 提取投注占比
    bet_pct_win = p.get('主胜', {}).get('bet_pct', '')
    bet_pct_draw = p.get('平局', {}).get('bet_pct', '')
    bet_pct_lose = p.get('客胜', {}).get('bet_pct', '')
    
    # 提取成交量
    vol_win = p.get('主胜', {}).get('volume', '')
    vol_draw = p.get('平局', {}).get('volume', '')
    vol_lose = p.get('客胜', {}).get('volume', '')
    
    # 庄家盈亏
    profit_win = p.get('主胜', {}).get('profit_raw', '')
    profit_draw = p.get('平局', {}).get('profit_raw', '')
    profit_lose = p.get('客胜', {}).get('profit_raw', '')
    
    # 分析
    analysis = s26.get('analysis', {})
    zzhk = analysis.get('庄家最看好', '')
    
    matches.append({
        'matchnum': matchnum,
        'league': league,
        'home': home,
        'away': away,
        'macau': macau,
        'combo': combo,
        'bet_pct': f'{bet_pct_win}/{bet_pct_draw}/{bet_pct_lose}',
        'volume': f'{vol_win}/{vol_draw}/{vol_lose}',
        'profit': f'{profit_win}/{profit_draw}/{profit_lose}',
        'zzhk': zzhk,
    })

print(f'数据: {len(matches)}场')

# 按盘口分组统计
from collections import defaultdict
macau_groups = defaultdict(list)
for m in matches:
    macau_groups[m['macau']].append(m)

# 按联赛分组
league_groups = defaultdict(list)
for m in matches:
    league_groups[m['league']].append(m)

# 生成报告
report = []
report.append('# 竞彩30场分析报告（2026-05-09）')
report.append('')
report.append(f'📅 日期: 2026-05-09')
report.append(f'📊 场次: {len(matches)}场')
report.append(f'🏆 联赛: {", ".join(sorted(league_groups.keys()))}')
report.append('')

# 第一部分: 盘口 × 盈亏组合分析
report.append('## 一、澳门即时盘 × 盈亏方向组合分析')
report.append('')
report.append('| 盘口 | 盈亏组合 | 场次 | 占比 | 庄家偏好 |')
report.append('|------|---------|------|------|---------|')

macau_order = ['平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半', '球半',
               '受平手/半球', '受半球', '受半球/一球', '受一球', '受一球/球半', '受球半']

for macau in macau_order:
    if macau not in macau_groups:
        continue
    items = macau_groups[macau]
    
    # 统计盈亏组合
    combo_count = defaultdict(int)
    for m in items:
        combo_count[m['combo']] += 1
    
    for combo, count in sorted(combo_count.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(items) * 100
        
        # 解读
        meaning = ''
        if '胜赢' in combo: meaning += '庄家看好主胜 '
        elif '胜亏' in combo: meaning += '主胜大热(庄家怕) '
        if '平赢' in combo: meaning += '庄家看好平 '
        elif '平亏' in combo: meaning += '平局大热(庄家怕) '
        if '负赢' in combo: meaning += '庄家看好客胜'
        elif '负亏' in combo: meaning += '客胜大热(庄家怕)'
        
        report.append(f'| {macau} | {combo} | {count} | {pct:.0f}% | {meaning} |')

# 第二部分: 联赛分组分析
report.append('')
report.append('## 二、联赛分组分析')
report.append('')

for league in sorted(league_groups.keys(), key=lambda x: len(league_groups[x]), reverse=True):
    items = league_groups[league]
    report.append(f'### {league}（{len(items)}场）')
    report.append('')
    report.append('| 竞彩编号 | 对阵 | 即时盘 | 盈亏组合 | 投注占比(胜/平/负) | 庄家最看好 |')
    report.append('|---------|------|--------|---------|-----------------|-----------|')
    
    for m in sorted(items, key=lambda x: x['matchnum']):
        report.append(f'| {m["matchnum"]} | {m["home"]}vs{m["away"]} | {m["macau"]} | {m["combo"]} | {m["bet_pct"]} | {m["zzhk"]} |')

# 第三部分: 关键发现
report.append('')
report.append('## 三、关键发现')
report.append('')

# 统计盈亏方向
win_stats = {'赚': 0, '亏': 0}
draw_stats = {'赚': 0, '亏': 0}
lose_stats = {'赚': 0, '亏': 0}

for m in matches:
    combo = m['combo']
    if '胜赢' in combo: win_stats['赚'] += 1
    elif '胜亏' in combo: win_stats['亏'] += 1
    if '平赢' in combo: draw_stats['赚'] += 1
    elif '平亏' in combo: draw_stats['亏'] += 1
    if '负赢' in combo: lose_stats['赚'] += 1
    elif '负亏' in combo: lose_stats['亏'] += 1

total = len(matches)
report.append(f'### 庄家盈亏方向汇总（{total}场）')
report.append('')
report.append('| 方向 | 庄家赚(冷门) | 庄家亏(大热) | 庄家偏好 |')
report.append('|------|-------------|-------------|---------|')

win_pct = win_stats['赚'] / total * 100
draw_pct = draw_stats['赚'] / total * 100
lose_pct = lose_stats['赚'] / total * 100

report.append(f'| 主胜 | {win_stats["赚"]}场({win_pct:.0f}%) | {win_stats["亏"]}场({100-win_pct:.0f}%) | {"庄家看好主胜" if win_pct > 50 else "主胜大热"} |')
report.append(f'| 平局 | {draw_stats["赚"]}场({draw_pct:.0f}%) | {draw_stats["亏"]}场({100-draw_pct:.0f}%) | {"庄家看好平局" if draw_pct > 50 else "平局大热"} |')
report.append(f'| 客胜 | {lose_stats["赚"]}场({lose_pct:.0f}%) | {lose_stats["亏"]}场({100-lose_pct:.0f}%) | {"庄家看好客胜" if lose_pct > 50 else "客胜大热"} |')

# 第四部分: 投注建议
report.append('')
report.append('## 四、投注建议')
report.append('')

# 按盘口给出建议
for macau in macau_order:
    if macau not in macau_groups:
        continue
    items = macau_groups[macau]
    
    # 统计该盘口的盈亏组合
    combo_count = defaultdict(int)
    for m in items:
        combo_count[m['combo']] += 1
    
    # 找最常见的组合
    most_common = max(combo_count.items(), key=lambda x: x[1])
    combo, count = most_common
    pct = count / len(items) * 100
    
    # 给出建议
    suggestion = ''
    if '胜赢' in combo and '负亏' in combo:
        suggestion = '✅ 看好主胜，避开客胜'
    elif '胜亏' in combo and '负赢' in combo:
        suggestion = '✅ 看好客胜，避开主胜'
    elif '平赢' in combo:
        suggestion = '⚠️ 平局冷门，可补单'
    elif '平亏' in combo:
        suggestion = '⚠️ 平局大热，庄家怕平'
    else:
        suggestion = '🔄 方向不明，谨慎投注'
    
    report.append(f'- **{macau}**（{len(items)}场，{pct:.0f}%为{combo}）: {suggestion}')

# 保存报告
report_path = os.path.join('jingcai', 'tasks', '2026-05-09', '分析报告_30场.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f'\n报告已保存: {report_path}')
print(f'报告内容:')
print('\n'.join(report[:50]))
print('...')
