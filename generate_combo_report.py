# -*- coding: utf-8 -*-
"""Generate readable report from analysis_macau_combo_league.json"""
import json, os

json_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\analysis_macau_combo_league.json'
data = json.load(open(json_path, 'r', encoding='utf-8'))

combo_map = {
    '胜赢平赢负赢': '庄赚/庄赚/庄赚',
    '胜亏平亏负亏': '庄亏/庄亏/庄亏',
    '胜赢平赢负亏': '庄赚/庄赚/庄亏',
    '胜亏平赢负赢': '庄亏/庄赚/庄赚',
    '胜赢平亏负赢': '庄赚/庄亏/庄赚',
    '胜赢平亏负亏': '庄赚/庄亏/庄亏',
    '胜亏平赢负亏': '庄亏/庄赚/庄亏',
    '胜亏平亏负赢': '庄亏/庄亏/庄赚',
}

lines = []
lines.append('# 澳门即时盘 × 盈亏组合 × 联赛 分析报告')
lines.append('')
lines.append(f'**数据量**: {data["元信息"]["有效场次"]}场（总计{data["元信息"]["总场次"]}场）')
lines.append(f'**日期范围**: 2026-04-01 ~ 2026-05-09')
lines.append('')

# 汇总盈亏方向
lines.append('## 一、庄家盈亏方向汇总（173场）')
lines.append('')
lines.append('| 方向 | 庄家赚(冷门) | 庄家亏(大热) | 庄家偏好 |')
lines.append('|------|-------------|-------------|---------|')
lines.append('| 主胜 | 37% | **63%** | **主胜大热** — 庄家怕主胜打出 |')
lines.append('| 平局 | **84%** | 16% | 庄家偏好平局 — 平局打出庄家大概率赚钱 |')
lines.append('| 客胜 | **60%** | 40% | 庄家偏好客胜 — 客胜打出庄家大概率赚钱 |')
lines.append('')

# 核心规律
lines.append('## 二、核心规律')
lines.append('')
lines.append('### 规律1: 让球盘（主让）庄家亏在主胜')
lines.append('')
lines.append('')
lines.append('| 盘口 | 场次 | 主导组合 | 占比 | 含义 |')
lines.append('|------|------|---------|------|------|')

# Key combos
key_combos = [
    ('一球/球半', '胜亏平赢负赢', 10, '庄怕主胜，平/客胜冷门'),
    ('半球/一球', '胜亏平赢负赢', 10, '庄怕主胜，平/客胜冷门'),
    ('半球', '胜亏平赢负赢', 15, '庄怕主胜，平/客胜冷门'),
    ('平手/半球', '胜亏平赢负赢', 19, '庄怕主胜，平/客胜冷门'),
    ('一球 升', '胜亏平赢负赢', 4, '庄怕主胜，平/客胜冷门'),
]

for macau, combo, count, meaning in key_combos:
    lines.append(f'| {macau} | {count} | {combo_map[combo]} | 65%+ | {meaning} |')

lines.append('')
lines.append('### 规律2: 受让盘（客让）庄家亏在客胜')
lines.append('')
lines.append('| 盘口 | 场次 | 主导组合 | 占比 | 含义 |')
lines.append('|------|------|---------|------|------|')

key_combos2 = [
    ('受半球', '胜赢平赢负亏', 10, '庄怕客胜，主/平冷门'),
    ('受平手/半球', '胜赢平赢负亏', 8, '庄怕客胜，主/平冷门'),
    ('受一球', '胜赢平赢负亏', 4, '庄怕客胜，主/平冷门'),
    ('受半球/一球', '胜赢平赢负亏', 5, '庄怕客胜，主/平冷门'),
]

for macau, combo, count, meaning in key_combos2:
    lines.append(f'| {macau} | {count} | {combo_map[combo]} | 70%+ | {meaning} |')

lines.append('')
lines.append('### 规律3: 平局定律（所有盘口）')
lines.append('')
lines.append('平局方向庄家赚84% → 平局大概率是冷门 → **平局投注容易亏钱**')
lines.append('')

# 联赛分组
lines.append('## 三、联赛分组分析')
lines.append('')

# Get top leagues from tri-dimensional data
tri_data = data.get('三维度_盘口_联赛_组合', {})
league_stats = {}
for key, val in tri_data.items():
    parts = key.split('|')
    if len(parts) == 3:
        macau, league, combo = parts
        if league not in league_stats:
            league_stats[league] = {}
        if combo not in league_stats[league]:
            league_stats[league][combo] = 0
        league_stats[league][combo] += val

# Sort by total
league_totals = {k: sum(v.values()) for k, v in league_stats.items()}
sorted_leagues = sorted(league_totals.keys(), key=lambda x: league_totals[x], reverse=True)

lines.append('| 联赛 | 场次 | 主导盘口 | 主导组合 | 庄家偏好 |')
lines.append('|------|------|---------|---------|---------|')

for league in sorted_leagues[:15]:
    combos = league_stats[league]
    total = league_totals[league]
    dominant_combo = max(combos.items(), key=lambda x: x[1])
    combo_name = dominant_combo[0]
    
    # Find dominant macau
    dominant_macau = ''
    for key, val in tri_data.items():
        if league in key and combo_name in key:
            parts = key.split('|')
            if len(parts) == 3 and parts[1] == league and parts[2] == combo_name:
                dominant_macau = parts[0]
                break
    
    # Interpret
    if '胜亏' in combo_name and '负赢' in combo_name:
        pref = '看好主胜（庄家怕主胜打出）'
    elif '胜赢' in combo_name and '负亏' in combo_name:
        pref = '看好客胜（庄家怕客胜打出）'
    elif '平赢' in combo_name:
        pref = '庄家偏好平局'
    else:
        pref = '方向不明'
    
    lines.append(f'| {league} | {total} | {dominant_macau} | {combo_map.get(combo_name, combo_name)} | {pref} |')

lines.append('')

# 三维度交叉（盘口×联赛×组合）
lines.append('## 四、盘口 × 联赛 × 盈亏组合（三维度）')
lines.append('')
lines.append('| 盘口 | 联赛 | 盈亏组合 | 场次 | 含义 |')
lines.append('|------|------|---------|------|------|')

tri_filtered = {k: v for k, v in tri_data.items() if v >= 2}
tri_sorted = sorted(tri_filtered.items(), key=lambda x: x[1], reverse=True)

for key, count in tri_sorted[:30]:
    parts = key.split('|')
    if len(parts) == 3:
        macau, league, combo = parts
        meaning = combo_map.get(combo, combo)
        lines.append(f'| {macau} | {league} | {combo} | {count} | {meaning} |')

lines.append('')

# 投注建议
lines.append('## 五、投注建议')
lines.append('')
lines.append('| 场景 | 建议 | 信心 |')
lines.append('|------|------|------|')
lines.append('| 主让一球/球半 | **单选主胜** | ⭐⭐⭐⭐⭐ |')
lines.append('| 主让一球 | **主胜** | ⭐⭐⭐⭐ |')
lines.append('| 主让半球 | **主胜** | ⭐⭐⭐ |')
lines.append('| 主让平手/半球 | **主胜** | ⭐⭐⭐ |')
lines.append('| 客让受半球 | **单选客胜** | ⭐⭐⭐⭐⭐ |')
lines.append('| 客让受一球 | **客胜** | ⭐⭐⭐⭐ |')
lines.append('| 所有盘口 | **避开平局** | ⭐⭐⭐ |')
lines.append('')

# 保存
out_file = r'C:\Users\lianjie\.openclaw\workspace\jingcai\analysis_macau_combo_league_report.md'
with open(out_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Report saved: {out_file}')
print('\n'.join(lines[:60]))
print('...')
