# -*- coding: utf-8 -*-
"""从反馈机制获取比分，重新跑组合分析"""
import os, json, requests, re
from collections import defaultdict

# 1. 从zgzcw.com获取开奖结果
def fetch_zgzcw_scores():
    url = 'https://cp.zgzcw.com/dc/getKaijiangFootBall.action'
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://cp.zgzcw.com/',
        }, timeout=15)
        resp.encoding = 'utf-8'
        
        score_map = {}
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', resp.text, re.DOTALL)
        for row in rows:
            num_match = re.search(r'(周[一二三四五六日]\d+)', row)
            if not num_match:
                continue
            match_num = num_match.group(1)
            
            score_match = re.search(r'(\d{1,2})[：:](\d{1,2})\s*\(\d{1,2}[：:]\d{1,2}\)', row)
            if not score_match:
                continue
            
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))
            score_map[match_num] = f'{home_score}:{away_score}'
        
        return score_map
    except Exception as e:
        print(f'获取比分失败: {e}')
        return {}

print('从zgzcw.com获取比分...')
score_map = fetch_zgzcw_scores()
print(f'获取到 {len(score_map)} 场比分')

# 2. 写入meta.json
BASE = os.path.join('jingcai', 'tasks')
updated = 0

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        matchnum = meta.get('matchnum', '')
        
        if matchnum in score_map:
            meta['score'] = score_map[matchnum]
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            updated += 1

print(f'更新 {updated} 场meta.json')

# 3. 重新跑组合分析
print('\n重新跑组合分析...')

records = []
total = 0

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
            continue
        
        score = meta.get('score', '')
        if not score or ':' not in score:
            continue
        
        # 获取实际胜平负
        parts = score.split(':')
        try:
            home, away = int(parts[0]), int(parts[1])
            if home > away:
                actual = '胜'
            elif home == away:
                actual = '平'
            else:
                actual = '负'
        except:
            continue
        
        league = meta.get('league', '')
        
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
        })

print(f'有效数据: {len(records)}场 (总{total}场)')

# 4. 分析: 盘口 × 盈亏组合 → 胜平负概率
combo_groups = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in records:
    key = (r['macau'], r['combo'])
    combo_groups[key]['count'] += 1
    combo_groups[key][r['actual']] += 1

# 5. 联赛 × 盈亏组合
league_combo = defaultdict(lambda: defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0}))
for r in records:
    league_combo[r['league']][r['combo']]['count'] += 1
    league_combo[r['league']][r['combo']][r['actual']] += 1

# 6. 三维度: 盘口 × 联赛 × 盈亏组合
tri = defaultdict(lambda: {'count': 0, '胜': 0, '平': 0, '负': 0})
for r in records:
    key = (r['macau'], r['league'], r['combo'])
    tri[key]['count'] += 1
    tri[key][r['actual']] += 1

# 7. 输出报告
print('\n' + '='*120)
print('澳门即时盘 × 盈亏组合 → 胜平负概率 (样本≥3)')
print('='*120)

print(f'\n{"盘口":<18} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>6} | {"平(%)":>6} | {"负(%)":>6} | 最大概率')
print('-'*120)

# 按盘口顺序
macau_order = ['平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半', '球半',
               '受平手/半球', '受半球', '受半球/一球', '受一球', '受一球/球半', '受球半']

current_macau = None
for macau in macau_order:
    for (m, c), v in sorted(combo_groups.items()):
        if m != macau or v['count'] < 3:
            continue
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        # 标注显著信号
        sig = []
        if win_pct >= 70: sig.append(f'胜↑')
        if lose_pct >= 70: sig.append(f'负↑')
        if draw_pct <= 15: sig.append(f'平↓')
        sig_str = ','.join(sig) if sig else ''
        
        prefix = macau if current_macau != macau else ''
        current_macau = macau
        
        print(f'{prefix:<18} | {c:<16} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# 8. 联赛分组
print('\n' + '\n' + '='*120)
print('联赛 × 盈亏组合 → 胜平负概率 (样本≥3)')
print('='*120)

print(f'\n{"联赛":<12} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>6} | {"平(%)":>6} | {"负(%)":>6} | 最大概率')
print('-'*120)

league_totals = {league: sum(c.values()) for league, combos in league_combo.items() for c in combos.values()}
sorted_leagues = sorted(league_totals.keys(), key=lambda x: league_totals[x], reverse=True)

for league in sorted_leagues[:10]:
    combos = league_combo[league]
    sorted_combos = sorted(combos.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for combo, v in sorted_combos:
        if v['count'] < 3:
            continue
        win_pct = v['胜'] / v['count'] * 100
        draw_pct = v['平'] / v['count'] * 100
        lose_pct = v['负'] / v['count'] * 100
        
        probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
        max_dir, max_pct = max(probs, key=lambda x: x[1])
        
        sig = []
        if win_pct >= 70: sig.append(f'胜↑')
        if lose_pct >= 70: sig.append(f'负↑')
        if draw_pct <= 15: sig.append(f'平↓')
        sig_str = ','.join(sig) if sig else ''
        
        print(f'{league:<12} | {combo:<16} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# 9. 三维度
print('\n' + '\n' + '='*120)
print('盘口 × 联赛 × 盈亏组合 (样本≥2)')
print('='*120)

print(f'\n{"盘口":<18} | {"联赛":<12} | {"盈亏组合":<16} | {"场次":>4} | {"胜(%)":>6} | {"平(%)":>6} | {"负(%)":>6} | 最大概率')
print('-'*120)

tri_filtered = {k: v for k, v in tri.items() if v['count'] >= 2}
tri_sorted = sorted(tri_filtered.items(), key=lambda x: x[1]['count'], reverse=True)

for (macau, league, combo), v in tri_sorted[:30]:
    win_pct = v['胜'] / v['count'] * 100
    draw_pct = v['平'] / v['count'] * 100
    lose_pct = v['负'] / v['count'] * 100
    
    probs = [('胜', win_pct), ('平', draw_pct), ('负', lose_pct)]
    max_dir, max_pct = max(probs, key=lambda x: x[1])
    
    sig = []
    if win_pct >= 70: sig.append(f'胜↑')
    if lose_pct >= 70: sig.append(f'负↑')
    if draw_pct <= 15: sig.append(f'平↓')
    sig_str = ','.join(sig) if sig else ''
    
    print(f'{macau:<18} | {league:<12} | {combo:<16} | {v["count"]:>4} | {win_pct:>6.1f}% | {draw_pct:>6.1f}% | {lose_pct:>6.1f}% | {max_dir}({max_pct:.0f}%) {sig_str}')

# 10. 保存JSON
output = {
    '元信息': {'总场次': total, '有效场次': len(records), '有比分': len(records)},
    '盘口_盈亏组合_胜平负': {f'{k[0]}|{k[1]}': v for k, v in combo_groups.items()},
    '联赛_盈亏组合_胜平负': {f'{k[0]}|{k[1]}': v for league, combos in league_combo.items() for k, v in combos.items()},
    '三维度_盘口_联赛_组合_胜平负': {f'{k[0]}|{k[1]}|{k[2]}': v for k, v in tri.items()},
}

out_file = os.path.join('jingcai', 'analysis_macau_combo_league_with_scores.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n完整JSON已保存: {out_file}')
