# -*- coding: utf-8 -*-
"""B方案：从联赛缓存提取原始赔率特征矩阵
   完全独立，不碰现有pipeline和数据
"""
import json, os, csv
import numpy as np
from collections import defaultdict

CACHE_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache'
OUT_DIR   = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

FEATURE_NAMES = [
    'home_win_odds',      # WIN
    'draw_odds',           # DRAW
    'away_win_odds',       # LOST
    'handicap_line',       # HANDICAPLINE
    'home_moneyline',      # HOMEMONEYLINE
    'away_moneyline',      # AWAYMONEYLINE
    'implied_prob_home',   # 1/WIN / (1/WIN+1/DRAW+1/LOST)
    'odds_diff_draw',      # DRAW - WIN
    'odds_diff_away',      # LOST - WIN
]

RESULT_MAP = {'主胜': '胜', '平局': '平', '客胜': '负'}


def extract_match_features(m):
    try:
        win  = float(m.get('WIN'))
        draw = float(m.get('DRAW'))
        lost = float(m.get('LOST'))
    except (TypeError, ValueError):
        return None
    try:
        hc = float(m.get('HANDICAPLINE')) if m.get('HANDICAPLINE') not in (None, '') else 0.0
    except (TypeError, ValueError):
        hc = 0.0
    try:
        home_ml = float(m.get('HOMEMONEYLINE')) if m.get('HOMEMONEYLINE') is not None else 0.0
        away_ml = float(m.get('AWAYMONEYLINE')) if m.get('AWAYMONEYLINE') is not None else 0.0
    except (TypeError, ValueError):
        home_ml = 0.0; away_ml = 0.0
    total_implied = 1.0/win + 1.0/draw + 1.0/lost
    imp_home = (1.0/win) / total_implied if total_implied > 0 else 0.0
    return [win, draw, lost, hc, home_ml, away_ml, imp_home, draw-win, lost-win]


def extract_target(m):
    c = m.get('_computed', {})
    if not c:
        return None
    return RESULT_MAP.get(c.get('match_result'))


def build_feature_matrix():
    fnames = sorted([f for f in os.listdir(CACHE_DIR) if f.endswith('.json')])
    print(f'共 {len(fnames)} 个联赛缓存文件')

    all_features = []
    all_targets = []
    all_meta = []

    leagues_processed = 0; leagues_skipped = 0
    matches_loaded = 0; matches_used = 0
    skip_no_target = 0; skip_no_feat = 0

    for fname in fnames:
        league = fname.replace('.json', '')
        fpath = os.path.join(CACHE_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            leagues_skipped += 1
            continue
        matches = data.get('all_matches', [])
        if not matches:
            leagues_skipped += 1
            continue

        leagues_processed += 1
        for m in matches:
            matches_loaded += 1
            target = extract_target(m)
            if target is None or target not in ('胜', '平', '负'):
                skip_no_target += 1
                continue
            feats = extract_match_features(m)
            if feats is None:
                skip_no_feat += 1
                continue
            all_features.append(feats)
            all_targets.append(target)
            all_meta.append({
                'league': data.get('league', league),
                'date': m.get('MATCHDATE', ''),
                'home': m.get('HOMETEAMSXNAME', ''),
                'away': m.get('AWAYTEAMSXNAME', ''),
                'hs': m.get('HOMESCORE', ''),
                'as': m.get('AWAYSCORE', ''),
            })
            matches_used += 1

        if leagues_processed % 100 == 0:
            print(f'  处理 {leagues_processed}/{len(fnames)} 联赛... ({matches_used} 条)')

    print(f'\n{"="*50}')
    print(f'处理完成:')
    print(f'  联赛: {leagues_processed} 个 (跳过{leagues_skipped})')
    print(f'  总比赛: {matches_loaded}')
    print(f'  无赛果跳过: {skip_no_target}')
    print(f'  缺赔率跳过: {skip_no_feat}')
    print(f'  最终样本: {matches_used}')

    # 赛果分布
    dist = defaultdict(int)
    for t in all_targets:
        dist[t] += 1
    print(f'\n赛果分布:')
    for label in ['胜', '平', '负']:
        n = dist.get(label, 0)
        print(f'  {label}: {n} ({n/len(all_targets)*100:.1f}%)')

    # 保存CSV
    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, 'cache_feature_matrix.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(FEATURE_NAMES + ['target'])
        for feats, tgt in zip(all_features, all_targets):
            w.writerow(feats + [tgt])
    print(f'\n✅ CSV已保存: {csv_path} ({matches_used}行)')

    # 保存JSON
    json_path = os.path.join(OUT_DIR, 'cache_feature_matrix.json')
    samples_out = []
    for feats, tgt, meta in zip(all_features, all_targets, all_meta):
        sample = dict(zip(FEATURE_NAMES, feats))
        sample['target'] = tgt
        sample.update(meta)
        samples_out.append(sample)

    json.dump({
        'n_samples': matches_used,
        'n_features': len(FEATURE_NAMES),
        'feature_names': FEATURE_NAMES,
        'distribution': dict(dist),
        'samples': samples_out,
    }, open(json_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'✅ JSON已保存: {json_path}')

    return all_features, all_targets, all_meta


if __name__ == '__main__':
    build_feature_matrix()
