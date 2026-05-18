# -*- coding: utf-8 -*-
"""批量补跑step25（庄家盈亏）+ 分组分析"""
import os, json, sys, time, subprocess

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

BASE = 'jingcai/tasks'
SCRIPT_DIR = 'jingcai'

# ===== 第一步：找出所有缺step25但有fid的match =====
print('=== 扫描缺step25的match ===')
missing = []  # (date, match_dir, meta)
dates_to_run = set()

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
        fid = meta.get('fid', '')
        if not fid:
            continue
        
        s25_path = os.path.join(mp, 'step25_zhuangjia.json')
        if os.path.exists(s25_path) and os.path.getsize(s25_path) > 0:
            continue  # 已有
        
        missing.append((d, mp, meta))
        dates_to_run.add(d)

print(f'缺step25: {len(missing)}场 (涉及{len(dates_to_run)}个日期)')
for dt in sorted(dates_to_run):
    count = sum(1 for x in missing if x[0] == dt)
    print(f'  {dt}: {count}场')

# ===== 第二步：逐日跑step25 =====
# 注意：step25_zhuangjia.py按日期跑，会自动处理该日期所有match
for dt in sorted(dates_to_run):
    print(f'\n>>> 跑 {dt} 的step25...')
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step25_zhuangjia.py'), dt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                               encoding='utf-8', errors='replace')
        if result.returncode == 0:
            # 提取关键输出
            for line in result.stdout.split('\n'):
                if '已保存' in line or 'OK' in line or '完成' in line or 'WARN' in line:
                    print(f'  {line.strip()}')
        else:
            print(f'  ERR: code={result.returncode}')
            if result.stderr:
                print(f'  STDERR: {result.stderr[:300]}')
    except subprocess.TimeoutExpired:
        print(f'  TIMEOUT: {dt}')
    except Exception as e:
        print(f'  ERROR: {e}')
    time.sleep(2)

# ===== 第三步：重新统计 =====
print('\n=== 补跑后统计 ===')
total_s25 = 0
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    for m in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, m)
        if not os.path.isdir(mp):
            continue
        s25 = os.path.join(mp, 'step25_zhuangjia.json')
        if os.path.exists(s25) and os.path.getsize(s25) > 0:
            total_s25 += 1

print(f'总step25: {total_s25}场')

# ===== 第四步：分组分析 =====
print('\n=== 澳门亚盘(即时) × 庄家盈亏方向 分组分析 ===')

# 收集所有有macau_line和step25的数据
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
        
        s25_path = os.path.join(mp, 'step25_zhuangjia.json')
        if not (os.path.exists(s25_path) and os.path.getsize(s25_path) > 0):
            continue
        
        s25 = json.load(open(s25_path, 'r', encoding='utf-8'))
        labels = s25.get('labels', {})
        if not labels:
            continue
        
        # 提取庄家盈亏方向（基于profit标签）
        profit_map = {}
        for cat in ['主胜', '平局', '客胜']:
            if cat in labels:
                profit_map[cat] = labels[cat].get('profit', '-')
        
        records.append({
            'date': d,
            'matchnum': meta.get('matchnum', ''),
            'match': meta.get('match', ''),
            'macau_line': macau,
            'profit': profit_map,
        })

print(f'有效记录: {len(records)}场 (有macau_line+step25)')

# 按macau_line分组
groups = {}
for r in records:
    key = r['macau_line']
    if key not in groups:
        groups[key] = []
    groups[key].append(r)

# 对每个亚盘组，统计庄家盈亏方向分布
print(f'\n共{len(groups)}种亚盘:')
for pan in sorted(groups.keys()):
    items = groups[pan]
    # 统计每个方向的庄家盈亏
    # 主胜: 赢/亏/?, 平局: 赢/亏/?, 客胜: 赢/亏/?
    zhuang_win = {'主胜': 0, '平局': 0, '客胜': 0}
    zhuang_loss = {'主胜': 0, '平局': 0, '客胜': 0}
    zhuang_unknown = {'主胜': 0, '平局': 0, '客胜': 0}
    
    for item in items:
        for cat in ['主胜', '平局', '客胜']:
            p = item['profit'].get(cat, '?')
            if p == '多':
                # profit=多表示庄家赚得多（赢钱）
                zhuang_win[cat] += 1
            elif p == '少':
                # profit=少表示庄家赚得少/亏钱
                zhuang_loss[cat] += 1
            else:
                zhuang_unknown[cat] += 1
    
    total = len(items)
    print(f'\n--- {pan} ({total}场) ---')
    for cat in ['主胜', '平局', '客胜']:
        w = zhuang_win[cat]
        l = zhuang_loss[cat]
        u = zhuang_unknown[cat]
        if w + l > 0:
            win_pct = w / (w + l) * 100
            print(f'  {cat}: 庄家赚{w}场({win_pct:.0f}%) / 庄家亏{l}场 | 未知{u}')
        else:
            print(f'  {cat}: 全部未知')

# 保存分析结果
output = {
    'total_records': len(records),
    'groups': {}
}
for pan in sorted(groups.keys()):
    items = groups[pan]
    total = len(items)
    zhuang_win = {'主胜': 0, '平局': 0, '客胜': 0}
    zhuang_loss = {'主胜': 0, '平局': 0, '客胜': 0}
    for item in items:
        for cat in ['主胜', '平局', '客胜']:
            p = item['profit'].get(cat, '?')
            if p == '多':
                zhuang_win[cat] += 1
            elif p == '少':
                zhuang_loss[cat] += 1
    
    output['groups'][pan] = {
        'count': total,
        'zhuang_win': zhuang_win,
        'zhuang_loss': zhuang_loss,
        'detail': [{'matchnum': r['matchnum'], 'match': r['match'], 'profit': r['profit']} for r in items[:20]]
    }

out_path = os.path.join(SCRIPT_DIR, 'analysis_macau_profit.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f'\n分析结果已保存: {out_path}')
