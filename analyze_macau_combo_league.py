# -*- coding: utf-8 -*-
"""
澳门即时盘 × 盈亏组合 × 联赛 三维交叉分析

数据源：
- meta.json: macau_line(即时盘)
- step26_profit_ratio.json: profit_dir(庄家盈亏方向)
- matches_data.json: 实际比分

盈亏组合: 胜X平X负X (赢=庄家赚钱，亏=庄家亏钱)
"""
import os, json, re
from collections import defaultdict

BASE = os.path.join('jingcai', 'tasks')

def get_actual_result(score_str):
    """从比分字符串获取胜平负"""
    if not score_str or ':' not in score_str:
        return None
    parts = score_str.split(':')
    try:
        home, away = int(parts[0].strip()), int(parts[1].strip())
        if home > away: return '胜'
        elif home == away: return '平'
        else: return '负'
    except:
        return None

def get_profit_combo(step26_data):
    """从step26提取盈亏组合"""
    if not step26_data or 'profit_data' not in step26_data:
        return None
    p = step26_data['profit_data']
    
    win_dir = p.get('主胜', {}).get('profit_dir', None)
    draw_dir = p.get('平局', {}).get('profit_dir', None)
    lose_dir = p.get('客胜', {}).get('profit_dir', None)
    
    if win_dir is None or draw_dir is None or lose_dir is None:
        return None
    
    # True=庄家赚钱(冷门)，False=庄家亏钱(大热)
    win_label = '赢' if win_dir else '亏'
    draw_label = '赢' if draw_dir else '亏'
    lose_label = '赢' if lose_dir else '亏'
    
    return f'胜{win_label}平{draw_label}负{lose_label}'

# 收集所有数据
all_records = []
total_matches = 0
missing_macau = 0
missing_s26 = 0
missing_score = 0

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    # 读取matches_data.json获取比分
    matches_json = os.path.join(dp, 'matches_data.json')
    match_scores = {}
    if os.path.exists(matches_json):
        md = json.load(open(matches_json, 'r', encoding='utf-8'))
        for group_name, group_data in md.get('groups', {}).items():
            if isinstance(group_data, dict) and 'matches' in group_data:
                for m in group_data['matches']:
                    matchnum = m.get('matchnum', '')
                    # 尝试多种方式获取比分
                    score = m.get('score', '') or m.get('result', '')
                    if score:
                        match_scores[matchnum] = score
    
    # 读取最终报告获取比分
    for f in sorted(os.listdir(dp)):
        if f.endswith('.md') and '周' in f:
            report_path = os.path.join(dp, f)
            content = open(report_path, 'r', encoding='utf-8', errors='replace').read()
            # 匹配: 实际比分: 2:1 或 比分: 2:1
            m = re.search(r'(?:实际)?比分[：:]\s*(\d+)\s*[:：\-]\s*(\d+)', content)
            if m:
                num_match = re.search(r'周[一二三四五六日]\d+', f)
                if num_match:
                    match_scores[num_match.group(0)] = f'{m.group(1)}:{m.group(2)}'
    
    for m in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, m)
        if not (os.path.isdir(mp) and m.startswith('match')):
            continue
        
        meta_path = os.path.join(mp, 'meta.json')
        s26_path = os.path.join(mp, 'step26_profit_ratio.json')
        
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        total_matches += 1
        
        macau_line = meta.get('macau_line', '')
        if not macau_line:
            missing_macau += 1
            continue
        
        matchnum = meta.get('matchnum', '')
        league = meta.get('league', '')
        
        # 获取比分
        score = meta.get('score', '') or match_scores.get(matchnum, '')
        actual = get_actual_result(score)
        if not actual:
            missing_score += 1
            continue
        
        # 获取step26盈亏组合
        if not os.path.exists(s26_path):
            missing_s26 += 1
            continue
        
        s26 = json.load(open(s26_path, 'r', encoding='utf-8'))
        combo = get_profit_combo(s26)
        if not combo:
            missing_s26 += 1
            continue
        
        all_records.append({
            'date': d,
            'matchnum': matchnum,
            'league': league,
            'macau': macau_line,
            'combo': combo,
            'actual': actual,
        })

print(f'数据: {len(all_records)}场 (总{total_matches}, 缺比分:{missing_score}, 缺组合:{missing_s26})')

# ========== 分析1: macau_line × 盈亏组合 → 胜平负概率 ==========
print('\n' + '='*140)
print('分析1: 澳门即时盘 × 盈亏方向组合 → 胜平负概率')
print('='*140)

combo_groups = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in all_records:
    key = (r['macau'], r['combo'])
    combo_groups[key]['count'] += 1
    combo_groups[key][r['actual']] += 1

# 按盘口和组合排序
print(f'\n{"盘口":<18} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>8} | {"平(%)":>8} | {"负(%)":>8} | 最大概率')
print('-'*140)

# 筛选样本≥3的组合
valid = {k: v for k, v in combo_groups.items() if v['count'] >= 3}

# 按盘口分组
macau_groups = defaultdict(list)
for (macau, combo), v in valid.items():
    macau_groups[macau].append((combo, v))

for macau in sorted(macau_groups.keys()):
    items = macau_groups[macau]
    # 按总场次排序
    items.sort(key=lambda x: x[1]['count'], reverse=True)
    
    first = True
    for combo, v in items:
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        # 最大概率
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        # 标注显著信号(≥60%)
        sig = []
        if win_pct >= 60: sig.append(f'胜↑')
        if draw_pct <= 20: sig.append(f'平↓')
        if lose_pct >= 60: sig.append(f'负↑')
        sig_str = ','.join(sig) if sig else ''
        
        if first:
            print(f'{macau:<18} | {combo:<16} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')
            first = False
        else:
            print(f'{"":<18} | {combo:<16} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# ========== 分析2: 联赛 × 盈亏组合 → 胜平负概率 ==========
print('\n' + '='*140)
print('分析2: 联赛 × 盈亏方向组合 → 胜平负概率 (样本≥3)')
print('='*140)

league_combo = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in all_records:
    key = (r['league'], r['combo'])
    league_combo[key]['count'] += 1
    league_combo[key][r['actual']] += 1

print(f'\n{"联赛":<14} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>8} | {"平(%)":>8} | {"负(%)":>8} | 最大概率')
print('-'*140)

league_groups = defaultdict(list)
for (league, combo), v in league_combo.items():
    if v['count'] >= 3:
        league_groups[league].append((combo, v))

for league in sorted(league_groups.keys()):
    items = league_groups[league]
    items.sort(key=lambda x: x[1]['count'], reverse=True)
    
    for combo, v in items:
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        sig = []
        if win_pct >= 60: sig.append(f'胜↑')
        if draw_pct <= 20: sig.append(f'平↓')
        if lose_pct >= 60: sig.append(f'负↑')
        sig_str = ','.join(sig) if sig else ''
        
        print(f'{league:<14} | {combo:<16} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# ========== 分析3: macau_line × 联赛 → 胜平负概率 ==========
print('\n' + '='*140)
print('分析3: 澳门即时盘 × 联赛 → 胜平负概率 (样本≥5)')
print('='*140)

macau_league = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in all_records:
    key = (r['macau'], r['league'])
    macau_league[key]['count'] += 1
    macau_league[key][r['actual']] += 1

print(f'\n{"盘口":<18} | {"联赛":<14} | {"场次":>4} | {"胜(%)":>8} | {"平(%)":>8} | {"负(%)":>8} | 最大概率')
print('-'*140)

ml_groups = defaultdict(list)
for (macau, league), v in macau_league.items():
    if v['count'] >= 5:
        ml_groups[macau].append((league, v))

for macau in sorted(ml_groups.keys()):
    items = ml_groups[macau]
    items.sort(key=lambda x: x[1]['count'], reverse=True)
    
    for league, v in items:
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        sig = []
        if win_pct >= 60: sig.append(f'胜↑')
        if draw_pct <= 20: sig.append(f'平↓')
        if lose_pct >= 60: sig.append(f'负↑')
        sig_str = ','.join(sig) if sig else ''
        
        print(f'{macau:<18} | {league:<14} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# ========== 保存完整JSON ==========
output = {
    '元信息': {
        '总场次': total_matches,
        '有效场次': len(all_records),
        '缺比分': missing_score,
        '缺盈亏组合': missing_s26,
        '缺macau_line': missing_macau,
        '日期范围': f'{d}' if all_records else '',
    },
    '分析1_盘口_盈亏组合': {f'{k[0]}|{k[1]}': v for k, v in combo_groups.items()},
    '分析2_联赛_盈亏组合': {f'{k[0]}|{k[1]}': v for k, v in league_combo.items()},
    '分析3_盘口_联赛': {f'{k[0]}|{k[1]}': v for k, v in macau_league.items()},
}

out_file = os.path.join('jingcai', 'analysis_macau_combo_league.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n完整JSON已保存: {out_file}')
