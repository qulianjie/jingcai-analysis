# -*- coding: utf-8 -*-
"""全量组合扫描器 V3 - 扫描所有可用的精细维度组合"""
import os, sys, json, re, glob
from collections import defaultdict
from itertools import combinations

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

print('=' * 70)
print('全量组合扫描器 V3')
print('=' * 70)

# 1. Load feedback data
fb_raw = json.loads(rd(FEEDBACK_FILE))
dates_data = fb_raw.get('dates', fb_raw)
print(f'\n[1] 加载反馈数据: {len(dates_data)} 个日期')

# 2. Collect all matches
all_matches = []
for date, date_info in sorted(dates_data.items()):
    if isinstance(date_info, dict):
        items = date_info.get('feedback', [])
        if not items:
            # Handle case where items might be direct objects
            if 'match_num' in date_info:
                items = [date_info]
        for item in items:
            combos = item.get('combos', {})
            s25 = item.get('s25', {})
            s26 = item.get('s26', {})
            
            all_matches.append({
                'date': date,
                'match_num': item.get('match_num', ''),
                'home': item.get('home', ''),
                'away': item.get('away', ''),
                'league': item.get('league', '未知'),
                'predicted': item.get('predicted', ''),
                'actual': item.get('actual', ''),
                'correct': item.get('correct', False),
                'rq_correct': item.get('rq_correct', False),
                'combo': combos,
                's25': s25,
                's26': s26,
            })

print(f'[2] 有效比赛: {len(all_matches)} 场')
total_correct = sum(1 for m in all_matches if m['correct'])
print(f'    预测正确: {total_correct}/{len(all_matches)} = {total_correct/len(all_matches)*100:.1f}%')

# Show sample of dimension values to debug
print(f'\n[Debug] Sample match s26 data:')
for m in all_matches[:1]:
    print(f'  combos: {json.dumps(m["combo"], ensure_ascii=False)[:200]}')
    print(f'  s25: {json.dumps(m["s25"], ensure_ascii=False)[:200]}')
    print(f'  s26: {json.dumps(m["s26"], ensure_ascii=False)[:200]}')

# 3. Define all available dimensions
dims = {
    # --- 基本面 ---
    '联赛': lambda m: m['league'],
    '竞彩预测': lambda m: m['predicted'],
    '信心': lambda m: str(m['combo'].get('confidence', '')) + '%',
    
    # --- 维度信号（利好主/利好客/中立）---
    '欧赔': lambda m: m['combo'].get('欧赔趋势_dir', ''),
    '让球': lambda m: m['combo'].get('让球趋势_dir', ''),
    '亚盘': lambda m: m['combo'].get('亚盘趋势_dir', ''),
    '百家': lambda m: m['combo'].get('百家对比_dir', ''),
    '庄家盈亏_粗': lambda m: m['combo'].get('庄家盈亏_dir', ''),
    
    # --- 精细盘路 ---
    '澳门亚盘': lambda m: m['combo'].get('澳门亚盘', ''),
    '竞彩盘路': lambda m: m['combo'].get('竞彩欧赔盘路', m['combo'].get('竞彩欧赔盘路_基准', '')),
    'IW盘路': lambda m: m['combo'].get('IW欧赔盘路', m['combo'].get('IW欧赔盘路_基准', '')),
    '百家盘路': lambda m: m['combo'].get('百家欧赔盘路', m['combo'].get('百家欧赔盘路_基准', '')),
    '澳门同赔': lambda m: max(m['combo'].get('澳门亚盘同赔分布', {}), key=m['combo'].get('澳门亚盘同赔分布', {}).get) if m['combo'].get('澳门亚盘同赔分布') else '',
    '让球盘路': lambda m: m['combo'].get('让球盘路_基准', ''),
    
    # --- 庄家盈亏精细 (step26 analysis) ---
    '庄家胜盈亏': lambda m: m['s26'].get('庄家胜盈亏', ''),
    '庄家平盈亏': lambda m: m['s26'].get('庄家平盈亏', ''),
    '庄家负盈亏': lambda m: m['s26'].get('庄家负盈亏', ''),
    '庄家看好': lambda m: m['s26'].get('庄家最看好', ''),
    
    # --- 投注占比精细 ---
    '投注主占比': lambda m: str(m['s26'].get('投注占比_主', '')),
    '投注平占比': lambda m: str(m['s26'].get('投注占比_平', '')),
    '投注负占比': lambda m: str(m['s26'].get('投注占比_客', '')),
    
    # --- 盈亏占比 ---
    '盈亏主占比': lambda m: str(m['s26'].get('盈亏占比_主', '')),
    '盈亏平占比': lambda m: str(m['s26'].get('盈亏占比_平', '')),
    '盈亏负占比': lambda m: str(m['s26'].get('盈亏占比_客', '')),
    
    # --- 澳门初盘 ---
    '澳门初盘': lambda m: m['combo'].get('澳门初盘', ''),
    '澳门即时盘': lambda m: m['combo'].get('澳门即时盘', ''),
    
    # --- 投注占比分级（从step25 labels）---
    '投注主分级': lambda m: m['s25'].get('主胜', {}).get('bet_pct', ''),
    '投注平分级': lambda m: m['s25'].get('平局', {}).get('bet_pct', ''),
    '投注负分级': lambda m: m['s25'].get('客胜', {}).get('bet_pct', ''),
}

dims_list = {}
seen = set()
for k, v in dims.items():
    if k not in seen:
        dims_list[k] = v
        seen.add(k)

print(f'\n[3] 可用维度: {len(dims_list)} 个')
for k in dims_list:
    vals = set()
    for m in all_matches:
        v = dims_list[k](m)
        if v:
            vals.add(str(v))
    print(f'    {k}: {len(vals)} 个值 ({", ".join(sorted(vals)[:5])}{"..." if len(vals)>5 else ""})')

# 4. Scan combos
print(f'\n[4] 扫描组合模式...')

def scan_combos(dim_names, min_samples=5, match_filter=None):
    """扫描指定维度组合的高准确率模式"""
    results = {}
    
    for match in all_matches:
        if match_filter and not match_filter(match):
            continue
        
        # Build key from dimension values
        parts = []
        has_empty = False
        for dname in dim_names:
            v = dims_list[dname](match)
            if not v:
                has_empty = True
                break
            parts.append(f'{dname}:{v}')
        
        if has_empty or not parts:
            continue
        
        combo_key = '×'.join(parts)
        if combo_key not in results:
            results[combo_key] = {'total': 0, 'correct': 0}
        
        results[combo_key]['total'] += 1
        if match['correct']:
            results[combo_key]['correct'] += 1
    
    # Filter by min_samples and sort by accuracy
    filtered = {}
    for k, v in results.items():
        if v['total'] >= min_samples:
            acc = v['correct'] / v['total']
            filtered[k] = (acc, v)
    
    return sorted(filtered.items(), key=lambda x: -x[1][0])

# 5. Show 2D combos
print('\n' + '=' * 70)
print('高准确率二维组合 (>=60%, >=5场)')
print('=' * 70)

top_2d = []
focus_dims = ['澳门亚盘', '竞彩盘路', 'IW盘路', '百家盘路', '庄家胜盈亏', '庄家平盈亏', '庄家负盈亏', 
              '庄家看好', '欧赔', '让球', '亚盘', '百家', '联赛', '竞彩预测', '澳门同赔',
              '投注主分级', '投注平分级', '投注负分级']

for d1, d2 in combinations(focus_dims, 2):
    results = scan_combos([d1, d2])
    for combo_key, (acc, stats) in results:
        if acc >= 0.60:
            top_2d.append((combo_key, acc, stats))

top_2d.sort(key=lambda x: (-x[1], -x[2]['total']))
for i, (combo_key, acc, stats) in enumerate(top_2d[:30]):
    print(f'{i+1:3d}. {combo_key}: {acc:.0%} ({stats["correct"]}/{stats["total"]})')

# 6. Show 3D combos (lower threshold: >=3 samples)
print('\n' + '=' * 70)
print('高准确率三维组合 (>=60%, >=3场)')
print('=' * 70)

top_3d = []
# Expand dimension set for 3D combos
focus_dims_3d = ['澳门亚盘', '竞彩盘路', 'IW盘路', '百家盘路', '庄家胜盈亏', '庄家平盈亏', '庄家负盈亏', 
              '庄家看好', '欧赔', '让球', '亚盘', '百家', '联赛', '竞彩预测', '澳门同赔',
              '投注主分级', '投注平分级', '投注负分级', '澳门初盘', '澳门即时盘']
for d1, d2, d3 in combinations(focus_dims_3d[:14], 3):
    results = scan_combos([d1, d2, d3], min_samples=3)
    for combo_key, (acc, stats) in results:
        if acc >= 0.60:
            top_3d.append((combo_key, acc, stats))

top_3d.sort(key=lambda x: (-x[1], -x[2]['total']))
for i, (combo_key, acc, stats) in enumerate(top_3d[:30]):
    print(f'{i+1:3d}. {combo_key}: {acc:.0%} ({stats["correct"]}/{stats["total"]})')

# 7. Show 4D combos (lower threshold: >=3 samples)
print('\n' + '=' * 70)
print('高准确率四维组合 (>=60%, >=3场)')
print('=' * 70)

top_4d = []
# Use a focused set of dimensions for 4D combos
focus_dims_4d = ['澳门亚盘', '竞彩盘路', 'IW盘路', '百家盘路', '庄家胜盈亏', '庄家平盈亏', '庄家负盈亏', 
              '欧赔', '亚盘', '百家', '联赛', '竞彩预测', '澳门同赔']
for d1, d2, d3, d4 in combinations(focus_dims_4d[:10], 4):
    results = scan_combos([d1, d2, d3, d4], min_samples=3)
    for combo_key, (acc, stats) in results:
        if acc >= 0.60:
            top_4d.append((combo_key, acc, stats))

top_4d.sort(key=lambda x: (-x[1], -x[2]['total']))
for i, (combo_key, acc, stats) in enumerate(top_4d[:30]):
    print(f'{i+1:3d}. {combo_key}: {acc:.0%} ({stats["correct"]}/{stats["total"]})')

# 8. Special: 预测=平 的组合
print('\n' + '=' * 70)
print('预测=平局 的高准确率组合')
print('=' * 70)

# Check actual predicted values
pred_vals = set(m['predicted'] for m in all_matches)
print(f'预测值样例: {pred_vals}')

draw_matches = [m for m in all_matches if m['predicted'] in ('平局', '平')]
print(f'预测=平的场次: {len(draw_matches)}')
if draw_matches:
    total_draw_correct = sum(1 for m in draw_matches if m['correct'])
    print(f'预测=平且正确: {total_draw_correct}/{len(draw_matches)} ({total_draw_correct/len(draw_matches)*100:.1f}%)')
    
    top_draw_2d = []
    for d1, d2 in combinations(focus_dims, 2):
        results = scan_combos([d1, d2], match_filter=lambda m: m['predicted'] in ('平局', '平'))
        for combo_key, (acc, stats) in results:
            if acc >= 0.50 and stats['total'] >= 3:
                top_draw_2d.append((combo_key, acc, stats))
    
    top_draw_2d.sort(key=lambda x: (-x[1], -x[2]['total']))
    for i, (combo_key, acc, stats) in enumerate(top_draw_2d[:20]):
        print(f'{i+1:3d}. {combo_key}: {acc:.0%} ({stats["correct"]}/{stats["total"]})')

# 9. Special: 预测=主胜 的组合
print('\n' + '=' * 70)
print('预测=主胜 的高准确率组合')
print('=' * 70)

win_matches = [m for m in all_matches if m['predicted'] in ('主胜', '胜')]
print(f'预测=主胜的场次: {len(win_matches)}')
if win_matches:
    total_win_correct = sum(1 for m in win_matches if m['correct'])
    print(f'预测=主胜且正确: {total_win_correct}/{len(win_matches)} ({total_win_correct/len(win_matches)*100:.1f}%)')
    
    top_win_2d = []
    for d1, d2 in combinations(focus_dims, 2):
        results = scan_combos([d1, d2], match_filter=lambda m: m['predicted'] in ('主胜', '胜'))
        for combo_key, (acc, stats) in results:
            if acc >= 0.60 and stats['total'] >= 3:
                top_win_2d.append((combo_key, acc, stats))
    
    top_win_2d.sort(key=lambda x: (-x[1], -x[2]['total']))
    for i, (combo_key, acc, stats) in enumerate(top_win_2d[:20]):
        print(f'{i+1:3d}. {combo_key}: {acc:.0%} ({stats["correct"]}/{stats["total"]})')

# 10. Special: 预测=客胜 的组合
print('\n' + '=' * 70)
print('预测=客胜 的高准确率组合')
print('=' * 70)

lose_matches = [m for m in all_matches if m['predicted'] in ('客胜', '负')]
print(f'预测=客胜的场次: {len(lose_matches)}')
if lose_matches:
    total_lose_correct = sum(1 for m in lose_matches if m['correct'])
    print(f'预测=客胜且正确: {total_lose_correct}/{len(lose_matches)} ({total_lose_correct/len(lose_matches)*100:.1f}%)')
    
    top_lose_2d = []
    for d1, d2 in combinations(focus_dims, 2):
        results = scan_combos([d1, d2], match_filter=lambda m: m['predicted'] in ('客胜', '负'))
        for combo_key, (acc, stats) in results:
            if acc >= 0.60 and stats['total'] >= 3:
                top_lose_2d.append((combo_key, acc, stats))
    
    top_lose_2d.sort(key=lambda x: (-x[1], -x[2]['total']))
    for i, (combo_key, acc, stats) in enumerate(top_lose_2d[:20]):
        print(f'{i+1:3d}. {combo_key}: {acc:.0%} ({stats["correct"]}/{stats["total"]})')

print('\n' + '=' * 70)
print('扫描完成!')
print('=' * 70)
