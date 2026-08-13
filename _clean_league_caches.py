#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清洗联赛缓存：剔除混入的其他级别/其他国家联赛场次（2026-08-14 修复）
规则：缓存文件名为 {league}.json，保留 SIMPLEGBNAME 与 league 匹配的场次。
备份原文件到 data/league_cache_clean_bak/
"""
import json, os, sys, shutil, time
from collections import Counter

SD = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SD, 'data', 'league_cache')
BAK_DIR = os.path.join(SD, 'data', 'league_cache_clean_bak')

sys.path.insert(0, SD)
from _league_util import _league_match

os.makedirs(BAK_DIR, exist_ok=True)
ts = time.strftime('%Y%m%d_%H%M%S')

# 只清洗指定联赛（参数），默认全部
targets = [a for a in sys.argv[1:] if a.endswith('.json')]

report = []
for fn in sorted(os.listdir(CACHE_DIR)):
    if not fn.endswith('.json'):
        continue
    if targets and fn not in targets:
        continue
    league = fn[:-5]
    path = os.path.join(CACHE_DIR, fn)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception as e:
        report.append(f'{fn}: 读取失败 {e}')
        continue

    allm = d.get('all_matches', [])
    if not allm:
        report.append(f'{fn}: 0场，跳过')
        continue

    # 统计
    before_cnt = len(allm)
    sg_before = Counter(m.get('SIMPLEGBNAME', '') for m in allm)

    kept = []
    dropped = []
    for m in allm:
        src_name = m.get('SIMPLEGBNAME', '')
        if _league_match(src_name, league):
            kept.append(m)
        else:
            dropped.append(src_name)

    if len(kept) == 0:
        report.append(f'{fn}: ⚠️ 清洗后0场（原{before_cnt}场），跳过不覆盖')
        continue

    # 备份
    bak_path = os.path.join(BAK_DIR, f'{fn}.{ts}.bak')
    shutil.copy2(path, bak_path)

    # 写回
    d['all_matches'] = kept
    d['match_count'] = len(kept)
    d['clean_date'] = time.strftime('%Y-%m-%d %H:%M')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    drop_info = ''
    if dropped:
        dc = Counter(dropped)
        drop_info = ' | 剔除: ' + ', '.join(f'{k}×{v}' for k, v in dc.most_common(5))
    report.append(f'{fn}: {before_cnt}→{len(kept)}场{drop_info}')

print('\n'.join(report))
print(f'\n备份目录: {BAK_DIR}')
