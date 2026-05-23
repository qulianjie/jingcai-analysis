# -*- coding: utf-8 -*-
"""
竞彩预测分析引擎 V2 - 多维度组合 + 历史模式匹配
新增：
1. 投注占比分析（step25）
2. 胜平负几率计算
3. 欧赔盘路组合匹配（≥2个欧赔盘路一致时加权）
4. 历史模式学习（从feedback.json学习高准确率组合）
"""
import os, sys, re, json, math
import sys as _sys
from datetime import datetime

def generate_conclusion(md_path):
    """Run full conclusion analysis for a match and return markdown text."""
    import os, json, re, math
    from _log_util import setup_logger
    from _util import rd, re_find, safe_json_load
    from conclusion_signals import analyze_zhuangjia, analyze_europe_odds, analyze_macau_asian, analyze_same_odds, analyze_home_team, analyze_away_team, analyze_baijia, analyze_panlu_match

    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(md_path)), "logs")
    log = setup_logger("final_concl", LOG_DIR)
    MD = md_path
    if not MD or not os.path.isdir(MD):
        log.info("Usage: python final_conclusion_generator.py <match_dir>")
        return ""

    G1 = os.path.join(MD, "group01_europe")
    G2 = os.path.join(MD, "group02_handicap")
    G3 = os.path.join(MD, "group03_asian")
    G4 = os.path.join(MD, "group04_teamA")
    G5 = os.path.join(MD, "group05_teamB")
    G6 = os.path.join(MD, "group06_baijia")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(MD)), "feedback.json")
    # ============ Paths ============
    G1 = os.path.join(MD, 'group01_europe')
    G2 = os.path.join(MD, 'group02_handicap')
    G3 = os.path.join(MD, 'group03_asian')
    G4 = os.path.join(MD, 'group04_teamA')
    G5 = os.path.join(MD, 'group05_teamB')
    G6 = os.path.join(MD, 'group06_baijia')

    FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'learnings', 'feedback.json')

    from _util import rd, re_find, ensure_utf8_stdout, safe_json_load
    from conclusion_signals import (
        analyze_europe_odds, analyze_same_odds, analyze_macau_asian,
        analyze_home_team, analyze_away_team, analyze_baijia,
        analyze_panlu_match, analyze_zhuangjia,
        _wilson, _bayesian, _trust_to_factor
    )
    ensure_utf8_stdout()

    # ============ Read all step data ============
    s1 = rd(os.path.join(G1, 'step1_europe_base.txt')) or rd(os.path.join(G1, 'step01_europe_basic.md'))
    s2 = rd(os.path.join(G1, 'step2_jingcai_same.txt')) or rd(os.path.join(G1, 'step02_jingcai_same.md'))
    s3 = rd(os.path.join(G1, 'step3_interwetten_same.txt')) or rd(os.path.join(G1, 'step03_interwetten_same.md'))
    s6 = rd(os.path.join(G3, 'step6_asian_base.txt')) or rd(os.path.join(G3, 'step06_asian_basic.md'))
    s7 = rd(os.path.join(G3, 'step7_macau_same.txt')) or rd(os.path.join(G3, 'step07_macau_same.md')) or rd(os.path.join(G3, 'step07_macau_same.json'))
    s8 = rd(os.path.join(G3, 'step8_same_league.txt')) or rd(os.path.join(G3, 'step08_same_league.md')) or rd(os.path.join(G3, 'step08_league_asian.md'))
    s9_13 = rd(os.path.join(G4, 'step9_home_history.txt')) or rd(os.path.join(G4, 'step09_13_teamA.md')) or rd(os.path.join(G4, 'step09_home_matches.md')) or rd(os.path.join(G4, 'step09_home_fixture.md'))
    s14_18 = rd(os.path.join(G5, 'step14_away_history.txt')) or rd(os.path.join(G5, 'step14_18_teamB.md')) or rd(os.path.join(G5, 'step14_away_matches.md')) or rd(os.path.join(G5, 'step14_away_fixture.md'))
    s19_23 = rd(os.path.join(G6, 'step19_baijia_compare.txt')) or rd(os.path.join(G6, 'step19_baijia_extract.md')) or rd(os.path.join(G6, 'step19_23_baijia.md'))
    s5 = rd(os.path.join(G2, 'step5_handicap_same.txt')) or rd(os.path.join(G2, 'step05_handicap_same.md'))

    # Step24
    s24_path = os.path.join(MD, 'step24_panlu_match.json')
    s24 = rd(s24_path)
    if not s24.strip():
        s24 = rd(os.path.join(os.path.dirname(MD), 'step24_panlu_match.json'))

    # Step25 - 从多个可能路径读取
    s25 = ''
    # 路径1: match目录本身
    s25_path = os.path.join(MD, 'step25_zhuangjia.json')
    if not os.path.exists(s25_path):
        # 路径2: 日期目录根（与data同级）
        s25_path = os.path.join(os.path.dirname(os.path.dirname(MD)), 'step25_zhuangjia.json')
    if not os.path.exists(s25_path):
        # 路径3: data子目录
        s25_path = os.path.join(os.path.dirname(os.path.dirname(MD)), 'data', 'step25_zhuangjia.json')
    if os.path.exists(s25_path):
        with open(s25_path, 'r', encoding='utf-8') as f:
            s25_data = json.loads(f.read())
        # 找到当前match的step25数据
        match_num = re_find(rd(os.path.join(MD, 'meta.json')), r'"matchnum":\s*"([^"]+)"')
        if match_num and s25_data.get('match_num') == match_num:
            s25 = json.dumps(s25_data, ensure_ascii=False)
    # ============ Load historical patterns ============
    def load_high_accuracy_patterns():
        """从learned_patterns.json / learned_patterns_v2.json加载学习到的模式 + 投注占比模式"""
        patterns = {
            'high_accuracy_combos': [],
            'low_accuracy_combos': [],
            'betting_patterns': {},
            'profit_patterns': {},
            'bet_profit_combo': {},
            'league_accuracy': {},
            'confidence_accuracy': {},
            'handicap_accuracy': {},
            'prediction_consistency': {},
            # V2 新增
            'league_ranked': [],
            'confidence_adjust': {},
            'profit_direction_accuracy': [],
            'panlu_accuracy': [],
            'combo_tags': {},
        }

        # 优先加载 V2 学习结果（包含组合分析+step25/26数据）
        learned_v2_file = os.path.join(os.path.dirname(__file__), 'learnings', 'learned_patterns_v2.json')
        if os.path.exists(learned_v2_file):
            try:
                with open(learned_v2_file, 'r', encoding='utf-8') as f:
                    learned_v2 = json.loads(f.read())
                patterns['league_ranked'] = learned_v2.get('league_accuracy', [])
                patterns['confidence_adjust'] = learned_v2.get('confidence_accuracy', {})
                patterns['profit_direction_accuracy'] = learned_v2.get('profit_direction_accuracy', [])
                patterns['panlu_accuracy'] = learned_v2.get('panlu_accuracy', [])
                patterns['high_accuracy_combos'] = learned_v2.get('high_accuracy_combos', [])
                patterns['low_accuracy_combos'] = learned_v2.get('low_accuracy_combos', [])
                patterns['handicap_accuracy'] = learned_v2.get('handicap_accuracy', {})
                patterns['prediction_consistency'] = learned_v2.get('prediction_consistency', {})
                patterns['_v2_loaded'] = True
                log.info(f'[LEARN] 已加载 V2 学习数据: {learned_v2.get("total_matches", 0)}场, 版本 {learned_v2.get("version", "?")}')
            except Exception as e:
                log.info(f'[LEARN] V2 学习数据加载失败: {e}')

        # 回退加载 V1（兼容旧数据）
        learned_file = os.path.join(os.path.dirname(__file__), 'learnings', 'learned_patterns.json')
        if os.path.exists(learned_file):
            try:
                with open(learned_file, 'r', encoding='utf-8') as f:
                    learned = json.loads(f.read())
                # 只在V2未加载时覆盖
                if not patterns.get('_v2_loaded'):
                    patterns['league_accuracy'] = learned.get('league_accuracy', {})
                    patterns['confidence_accuracy'] = learned.get('confidence_accuracy', {})
                    patterns['handicap_accuracy'] = learned.get('handicap_accuracy', {})
                    patterns['prediction_consistency'] = learned.get('prediction_consistency', {})
                    patterns['betting_patterns'] = learned.get('betting_patterns', {})
            except:

                log.warn(f"[final_concl] 解析异常")
        # Also load from feedback.json for combo analysis
        if not os.path.exists(FEEDBACK_FILE):
            return patterns

        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedback = json.loads(f.read())
        except:
            return patterns

        # 1. 统计combo准确率
        combo_stats = {}
        for date, date_data in feedback.get('dates', {}).items():
            for match in date_data.get('feedback', []):
                for combo_key, combo_data in match.get('combos', {}).items():
                    if not isinstance(combo_data, dict):
                        continue
                    if combo_key not in combo_stats:
                        combo_stats[combo_key] = {'total': 0, 'correct': 0}
                    combo_stats[combo_key]['total'] += combo_data.get('total', 0)
                    combo_stats[combo_key]['correct'] += combo_data.get('correct', 0)

        for combo, stats in combo_stats.items():
            if stats['total'] >= 3:
                accuracy = stats['correct'] / stats['total']
                if accuracy >= 0.60:
                    patterns['high_accuracy_combos'].append({
                        'name': combo, 'accuracy': accuracy,
                        'total': stats['total'], 'correct': stats['correct']
                    })
                elif accuracy <= 0.30:
                    patterns['low_accuracy_combos'].append({
                        'name': combo, 'accuracy': accuracy,
                        'total': stats['total'], 'correct': stats['correct']
                    })

        patterns['high_accuracy_combos'].sort(key=lambda x: x['accuracy'], reverse=True)
        patterns['low_accuracy_combos'].sort(key=lambda x: x['accuracy'])

        # 2. 学习投注占比差值模式
        # 从step25数据中提取投注占比差值，关联实际赛果
        bet_diff_buckets = {
            '0-5%': {'total': 0, 'correct': 0, 'results': []},
            '5-15%': {'total': 0, 'correct': 0, 'results': []},
            '15-25%': {'total': 0, 'correct': 0, 'results': []},
            '25-35%': {'total': 0, 'correct': 0, 'results': []},
            '35%+': {'total': 0, 'correct': 0, 'results': []},
        }

        profit_diff_buckets = {
            '0-3万': {'total': 0, 'correct': 0, 'results': []},
            '3-10万': {'total': 0, 'correct': 0, 'results': []},
            '10-30万': {'total': 0, 'correct': 0, 'results': []},
            '30万+': {'total': 0, 'correct': 0, 'results': []},
        }

        # 扫描所有match目录的step25数据
        tasks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks')
        if os.path.exists(tasks_dir):
            for date in os.listdir(tasks_dir):
                date_dir = os.path.join(tasks_dir, date)
                data_dir = os.path.join(date_dir, 'data')
                if not os.path.isdir(data_dir):
                    continue

                # 读取该日期的赛果
                results_file = os.path.join(os.path.dirname(__file__), f'results_{date}.json')
                if not os.path.exists(results_file):
                    continue

                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        results_data = json.loads(f.read()).get(date, {})
                except:
                    continue

                # 扫描match目录
                for match_dir in os.listdir(data_dir):
                    if not match_dir.startswith('match'):
                        continue

                    match_path = os.path.join(data_dir, match_dir)
                    s25_path = os.path.join(match_path, 'step25_zhuangjia.json')

                    if not os.path.exists(s25_path):
                        continue

                    try:
                        with open(s25_path, 'r', encoding='utf-8') as f:
                            s25 = json.loads(f.read())
                    except:
                        continue

                    s25_data = s25.get('data', {})
                    if not s25_data:
                        continue

                    # 提取投注占比
                    home_bet = float(s25_data.get('主胜', {}).get('bet_pct', '0') or '0')
                    draw_bet = float(s25_data.get('平局', {}).get('bet_pct', '0') or '0')
                    away_bet = float(s25_data.get('客胜', {}).get('bet_pct', '0') or '0')

                    bet_diff = max(home_bet, draw_bet, away_bet) - min(home_bet, draw_bet, away_bet)

                    # 提取盈亏
                    home_profit = float(s25_data.get('主胜', {}).get('profit', '0').replace(',', '') or '0')
                    draw_profit = float(s25_data.get('平局', {}).get('profit', '0').replace(',', '') or '0')
                    away_profit = float(s25_data.get('客胜', {}).get('profit', '0').replace(',', '') or '0')

                    profit_diff = max(home_profit, draw_profit, away_profit) - min(home_profit, draw_profit, away_profit)

                    # 找到对应赛果
                    match_num = s25.get('match_num', '')
                    actual = results_data.get(match_num, {}).get('result', '')
                    if not actual or actual == '待查':
                        continue

                    # 判断预测是否正确（简化：假设预测=实际）
                    # 这里需要更复杂的逻辑，暂时用实际结果标记
                    is_correct = True  # 占位，实际需要对比预测

                    # 放入桶中
                    if bet_diff < 5:
                        bet_diff_buckets['0-5%']['total'] += 1
                    elif bet_diff < 15:
                        bet_diff_buckets['5-15%']['total'] += 1
                    elif bet_diff < 25:
                        bet_diff_buckets['15-25%']['total'] += 1
                    elif bet_diff < 35:
                        bet_diff_buckets['25-35%']['total'] += 1
                    else:
                        bet_diff_buckets['35%+']['total'] += 1

                    if profit_diff < 30000:
                        profit_diff_buckets['0-3万']['total'] += 1
                    elif profit_diff < 100000:
                        profit_diff_buckets['3-10万']['total'] += 1
                    elif profit_diff < 300000:
                        profit_diff_buckets['10-30万']['total'] += 1
                    else:
                        profit_diff_buckets['30万+']['total'] += 1

        patterns['betting_patterns'] = bet_diff_buckets
        patterns['profit_patterns'] = profit_diff_buckets

        return patterns

    patterns = load_high_accuracy_patterns()
    log.info(f'[DEBUG] Loaded {len(patterns["high_accuracy_combos"])} high accuracy combos')
    # ============ Signal 9: 欧赔盘路组合匹配 ============
    # 分析>=2个欧赔盘路是否一致
    e1 = analyze_europe_odds(s1) if s1 else {}
    e2 = analyze_same_odds(s2, '竞彩') if s2 else {}
    e3 = analyze_same_odds(s3, 'IW') if s3 else {}

    directions = []
    if e1.get('score', 0) > 0.2: directions.append('home')
    elif e1.get('score', 0) < -0.2: directions.append('away')
    if e2.get('score', 0) > 0.2: directions.append('home')
    elif e2.get('score', 0) < -0.2: directions.append('away')
    if e3.get('score', 0) > 0.2: directions.append('home')
    elif e3.get('score', 0) < -0.2: directions.append('away')

    home_count = directions.count('home')
    away_count = directions.count('away')
    combo_score = 0
    combo_level = '无一致'
    if home_count >= 2:
        combo_score = 0.3 + (home_count - 2) * 0.1
        combo_level = f'{home_count}盘利好主'
    elif away_count >= 2:
        combo_score = -0.3 - (away_count - 2) * 0.1
        combo_level = f'{away_count}盘利好客'

    # ============ 执行所有信号分析 ============
    europe = analyze_europe_odds(s1)
    jc_same = analyze_same_odds(s2, "竞彩同赔")
    iw_same = analyze_same_odds(s3, "IW同赔")
    macau = analyze_macau_asian(s6, s7, s8)

    rq_same = analyze_same_odds(s5, "让球同赔") if s5 else {
        "score": 0, "total": 0, "win_rate": 0, "matched_dims": 0}

    home = analyze_home_team(s9_13)
    away = analyze_away_team(s14_18)
    baijia = analyze_baijia(s19_23)
    panlu = analyze_panlu_match(s24)
    zhuangjia = analyze_zhuangjia(s25)

    # ============ Signal 1: 欧赔趋势（step1）============
    def _parse_combo_dims_v3(tag):
        """从组合标签解析维度"""
        kw = {'竞彩': '竞彩同赔', 'IW': 'IW同赔', '盘路': '盘路匹配',
              '澳门': '澳门亚盘', '亚盘': '澳门亚盘', '让球': '让球同赔',
              '主队': '主队主场', '主场': '主队主场', '客队': '客队客场',
              '客场': '客队客场', '百家': '百家对比', '庄家': '庄家盈亏',
              '欧赔': '欧赔趋势'}
        dims = []
        for k, d in kw.items():
            if k in tag and d not in dims:
                dims.append(d)
        return dims if dims else ['欧赔趋势']

    # 获取当前联赛
    meta_path_combo = os.path.join(MD, 'meta.json')
    try:
        if os.path.exists(meta_path_combo):
            with open(meta_path_combo, 'r', encoding='utf-8') as f:
                _meta = json.loads(f.read())
            current_league = _meta.get('league', '')
    except:

        log.warn(f"[final_concl] 解析异常")
    # 构建比赛上下文
    match_ctx = {
        'league': current_league,
        'macau_line': '',
        'asian_dir': '',
        'oupei_dir': '',
        'rangqiu_dir': '',
        'baijia_dir': '',
        'zhuangjia_dir': '',
        'betting_ratio': '',
        'confidence_level': '',
    }

    # ============ 数据质量分 ============
    total_samples = (
        europe['total'] + jc_same['total'] + iw_same['total'] +
        macau['total'] + home['total'] + away['total'] + baijia['total'] +
        rq_same['total']
    )
    active_dims = sum(1 for x in [europe, jc_same, iw_same, macau, rq_same, home, away, baijia, panlu, zhuangjia]
                       if x.get('total', 0) > 0 or x.get('matched_dims', 0) > 0)
    data_quality = min(1.0, (total_samples / 60) * 0.5 + (active_dims / 10) * 0.5)

    # ============ 基础权重（10个维度，总权重=1.00）============
    base_weights = [
        ('欧赔趋势', europe['score'], 0.10),
        ('竞彩同赔', jc_same['score'], 0.12),
        ('IW同赔', iw_same['score'], 0.08),
        ('澳门亚盘', macau['score'], 0.10),
        ('让球同赔', rq_same['score'], 0.10),
        ('主队主场', home['score'], 0.12),
        ('客队客场', away['score'], 0.12),
        ('百家对比', baijia['score'], 0.10),
        ('盘路匹配', panlu['score'], 0.09),
        ('庄家盈亏', zhuangjia['score'], 0.07),
    ]

    # 从 base_weights 的 score 中提取方向信号
    for name, score, weight in base_weights:
        if abs(score) < 0.1:
            continue
        dir_str = '利好主' if score > 0 else '利好客'
        dmap = {'欧赔趋势': 'oupei_dir', '澳门亚盘': 'asian_dir',
                '让球同赔': 'rangqiu_dir', '百家对比': 'baijia_dir'}
        if name in dmap:
            match_ctx[dmap[name]] = dir_str

    # 从 combo 数据中提取额外上下文
    combo_data = locals().get('combo_data', {})
    if combo_data:
        match_ctx['macau_line'] = combo_data.get('澳门亚盘', '')
        match_ctx['betting_ratio'] = combo_data.get('投注占比', '')
        match_ctx['zhuangjia_dir'] = combo_data.get('庄家方向', '')
        match_ctx['confidence_level'] = combo_data.get('confidence_level', '')

    # 从 learned_patterns_v2.json 构建权重因子
    ew_factor = {}   # {dim_name: factor}
    adjust_log = []

    # 加载学习数据
    learned_v2_file = os.path.join(SCRIPT_DIR, 'learnings', 'learned_patterns_v2.json')
    learned_v2 = {}
    if os.path.exists(learned_v2_file):
        try:
            with open(learned_v2_file, 'r', encoding='utf-8') as f:
                learned_v2 = json.loads(f.read())
        except:

            log.warn(f"[final_concl] 解析异常")
    # ===== 1. 组合模式匹配 (Wilson Score) =====
    all_combos = learned_v2.get('high_accuracy_combos', []) + learned_v2.get('low_accuracy_combos', [])

    # 提取标签
    ctx_tags = []
    if current_league:
        ctx_tags.append(f'联赛:{current_league}')
    if match_ctx.get('asian_dir'):
        ctx_tags.append(f'亚盘:{match_ctx["asian_dir"]}')
    if match_ctx.get('oupei_dir'):
        ctx_tags.append(f'欧赔:{match_ctx["oupei_dir"]}')
    if match_ctx.get('rangqiu_dir'):
        ctx_tags.append(f'让球:{match_ctx["rangqiu_dir"]}')
    if match_ctx.get('baijia_dir'):
        ctx_tags.append(f'百家:{match_ctx["baijia_dir"]}')
    if match_ctx.get('zhuangjia_dir'):
        ctx_tags.append(f'庄家:{match_ctx["zhuangjia_dir"]}')
    if match_ctx.get('betting_ratio'):
        ctx_tags.append(f'投注占比:{match_ctx["betting_ratio"]}')
    if match_ctx.get('confidence_level'):
        ctx_tags.append(f'信心:{match_ctx["confidence_level"]}')

    # 匹配 combo
    best_combo = None
    best_precision = 0
    for combo in all_combos:
        tag = combo.get('tag', '')
        parts = [p.strip() for p in tag.split('×')]
        matched = sum(1 for p in parts if p in ctx_tags)
        if matched == len(parts) and len(parts) >= best_precision:
            correct = combo.get('correct', 0)
            total = combo.get('total', combo.get('n', 0))
            if total > 0:
                w = _wilson(correct, total)
                b = _bayesian(correct, total)
                trust = (w + b) / 2
                factor = _trust_to_factor(trust)
                is_low = combo in learned_v2.get('low_accuracy_combos', [])
                if len(parts) > best_precision or (len(parts) == best_precision and trust > (best_combo.get('trust', 0) if best_combo else 0)):
                    best_combo = {'tag': tag, 'factor': factor, 'trust': trust,
                                 'wilson': w, 'bayesian': b, 'accuracy': combo.get('accuracy', correct/total),
                                 'n': total, 'is_low': is_low, 'precision': len(parts)}
                    best_precision = len(parts)

    if best_combo:
        dims = _parse_combo_dims_v3(best_combo['tag'])
        tag_label = 'LOW-COMBO' if best_combo['is_low'] else 'HIGH-COMBO'
        for dim in dims:
            ew_factor[dim] = best_combo['factor']
            adjust_log.append(
                f'[{tag_label}] {best_combo["tag"]}: '
                f'trust={best_combo["trust"]:.3f}, '
                f'wilson={best_combo["wilson"]:.3f}, '
                f'bayesian={best_combo["bayesian"]:.3f}, '
                f'acc={best_combo["accuracy"]:.0%}({best_combo["n"]}场), '
                f'{dim} ×{best_combo["factor"]:.2f}')

    # ===== 2. 联赛准确率 (Wilson Score) =====
    league_ranked = learned_v2.get('league_accuracy', [])
    if current_league and league_ranked:
        for lr in league_ranked:
            if current_league in lr.get('league', ''):
                correct = lr.get('correct', 0)
                total = lr.get('total', 0)
                if total >= 3:
                    w = _wilson(correct, total)
                    b = _bayesian(correct, total)
                    trust = (w + b) / 2
                    lf = _trust_to_factor(trust)
                    adjust_log.append(
                        f'[LEAGUE] {lr["league"]}: '
                        f'trust={trust:.3f}, '
                        f'wilson={w:.3f}, '
                        f'bayesian={b:.3f}, '
                        f'acc={lr.get("accuracy", correct/total):.0%}({total}场), '
                        f'all dims ×{lf:.2f}')
                    for i, (name, score, weight) in enumerate(base_weights):
                        if abs(score) > 0.1:
                            ew_factor[name] = ew_factor.get(name, 1.0) * lf
                break

    # ===== 3. 专家盘路模式匹配 (V4 精确到小数点后一位) =====
    try:
        from expert_pattern_engine import ExpertPatternEngine
        ep_engine = ExpertPatternEngine(os.path.join(SCRIPT_DIR, 'learnings', 'expert_patterns.md'))

        # 提取赔率数据（从报告头部或step1数据）
        home_odds = away_odds = draw_odds = None
        step1_file = os.path.join(MD, 'group01_europe', 'step1_europe_base.txt')
        if os.path.exists(step1_file):
            try:
                with open(step1_file, 'r', encoding='utf-8') as f:
                    s1 = f.read()
                # 从表格提取竞彩官方赔率
                m = re.search(r'竞彩官方\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)', s1)
                if m:
                    home_odds = float(m.group(1))
                    draw_odds = float(m.group(2))
                    away_odds = float(m.group(3))
            except:

                log.warn(f"[final_concl] 解析异常")
        # 提取亚盘变化
        asian_line_val = match_ctx.get('macau_line', '')
        asian_change_val = ''
        asian_to_val = ''
        if asian_line_val and '→' in asian_line_val:
            parts = asian_line_val.split('→')
            asian_line_val = parts[0].strip()
            asian_to_val = parts[1].strip() if len(parts) > 1 else ''
            if '升' in asian_to_val:
                asian_change_val = '升'
            elif '降' in asian_to_val:
                asian_change_val = '降'

        # 调用专家引擎
        ep_factor, ep_pattern = ep_engine.match(
            league=current_league,
            home_odds=home_odds,
            away_odds=away_odds,
            draw_odds=draw_odds,
            odds_change=match_ctx.get('oupei_dir', ''),
            asian_line=asian_line_val,
            asian_change=asian_change_val,
            asian_to=asian_to_val,
        )

        if ep_factor and ep_pattern:
            adjust_log.append(
                f'[EXPERT] {ep_pattern["league"]} {ep_pattern["pattern"]} → {ep_pattern["outcome"]}: '
                f'×{ep_factor:.3f} (样本{ep_pattern["sample"]}场, 可信{ep_pattern["trust"]:.0%}, '
                f'匹配{ep_pattern["match_score"]:.0%}, {ep_pattern.get("note","")})')
            # 应用到所有有方向信号的维度
            for i, (name, score, weight) in enumerate(base_weights):
                if abs(score) > 0.1:
                    ew_factor[name] = ew_factor.get(name, 1.0) * ep_factor
    except ImportError:
        adjust_log.append('[EXPERT] 专家引擎模块未找到，跳过')
    except Exception as e:
        adjust_log.append(f'[EXPERT] 专家引擎异常: {e}')

    # ===== 4. 应用调整 =====
    new_weights = []
    for name, score, weight in base_weights:
        f = ew_factor.get(name, 1.0)
        nw = weight * f
        nw = max(0.05, min(0.30, nw))
        new_weights.append((name, score, nw))

    # ===== 5. 归一化 =====
    tw = sum(w for _, _, w in new_weights)
    if tw > 0:
        new_weights = [(n, s, w / tw) for n, s, w in new_weights]
    base_weights = new_weights

    # 输出调整日志
    for adj in adjust_log:
        log.info(adj)

    # 根据数据质量调整信心度
    quality_factor = 0.5 + data_quality * 0.5  # 0.5~1.0

    # 计算加权总分
    total_score = sum(score * weight for name, score, weight in base_weights)
    total_weight = sum(weight for name, score, weight in base_weights)
    final_score = total_score / total_weight if total_weight > 0 else 0
    # 不再用quality_factor压缩分值 - 数据质量应该只影响信心度，不影响预测方向
    # final_score = final_score * quality_factor  # 数据质量调整
    final_score = max(-1, min(1, final_score))

    # ============ Calculate confidence based on multiple factors ============
    abs_score = abs(final_score)

    # 信心度 = 分值大小 + 数据质量 + 维度一致性
    confidence_base = 40 + int(abs_score * 40)  # 基础信心40-80%
    confidence_quality = int(data_quality * 20)  # 数据质量加成0-20%
    confidence_consistency = 0

    # 维度一致性加分（已移除欧赔组合）

    confidence_pct = min(95, confidence_base + confidence_quality + confidence_consistency)

    # ============ V2 学习机制修正信心度 ============
    # 基于历史准确率修正信心值
    learn_adjustment_log = []

    # 1. 联赛历史准确率修正
    league_modifier = 0
    if patterns.get('league_ranked'):
        for lr in patterns['league_ranked']:
            league_name = lr.get('league', '')
            if current_league and current_league in league_name:
                league_acc = lr.get('accuracy', 0.5)
                if league_acc >= 0.6:
                    league_modifier = int((league_acc - 0.5) * 20)  # +2~+10
                    learn_adjustment_log.append(f'联赛{current_league}历史准确率{league_acc*100:.0f}% +{league_modifier}')
                elif league_acc <= 0.4:
                    league_modifier = int((league_acc - 0.5) * 20)  # -2~-10
                    learn_adjustment_log.append(f'联赛{current_league}历史准确率{league_acc*100:.0f}% {league_modifier}')
                break

    # 2. 盘路匹配度修正
    panlu_modifier = 0
    if patterns.get('panlu_accuracy'):
        for pa in patterns['panlu_accuracy']:
            level = pa.get('level', '')
            panlu_acc = pa.get('accuracy', 0.5)
            if level == '高' and panlu_acc >= 0.6:
                panlu_modifier = int((panlu_acc - 0.5) * 15)
                learn_adjustment_log.append(f'盘路匹配度高准确率{panlu_acc*100:.0f}% +{panlu_modifier}')
                break
            elif level == '低' and panlu_acc <= 0.4:
                panlu_modifier = -3
                learn_adjustment_log.append(f'盘路匹配度低准确率{panlu_acc*100:.0f}% {panlu_modifier}')
                break

    # 3. 高准确率组合标签修正
    tag_modifier = 0
    if patterns.get('high_accuracy_combos'):
        for hc in patterns['high_accuracy_combos'][:5]:
            tag = hc.get('tag', '')
            # 检查当前比赛是否匹配这些标签
            if current_league and f'联赛:{current_league}' == tag:
                acc = hc.get('accuracy', 0)
                if acc >= 0.65:
                    tag_modifier = int((acc - 0.5) * 15)
                    learn_adjustment_log.append(f'组合标签[{tag}]准确率{acc*100:.0f}% +{tag_modifier}')
                break

    # 应用修正
    learn_total = league_modifier + panlu_modifier + tag_modifier
    if learn_total != 0:
        confidence_pct = max(10, min(95, confidence_pct + learn_total))
        learn_adjustment_log.insert(0, f'学习修正总计: {learn_total:+d}')
        log.info(f'[LEARN] 信心度修正: {learn_total:+d} ({confidence_pct - learn_total}→{confidence_pct})')
        for adj2 in learn_adjustment_log:
            log.info(f'[LEARN]   {adj2}')

    # 信心等级
    if confidence_pct >= 70 and abs_score >= 0.4:
        confidence_level = '强'
    elif confidence_pct >= 55 and abs_score >= 0.25:
        confidence_level = '中'
    else:
        confidence_level = '弱'

    # 数据不足时建议回避
    if data_quality < 0.3 or active_dims < 3:
        confidence_level = '回避'
        confidence_pct = min(confidence_pct, 40)

    # ============ Generate text ============
    # 方向判断（调整阈值，减少平局误判）
    # 原来-0.25/+0.25太窄，大部分比赛分值落在这个区间，导致全是平局
    # 改为-0.05/+0.05，让大部分比赛有方向性
    if final_score > 0.05:
        direction = '主胜'
        direction_short = '主胜'
    elif final_score < -0.05:
        direction = '客胜'
        direction_short = '客胜'
    else:
        direction = '平局'
        direction_short = '平局'

    # 让球预测（必须与竞彩预测方向一致）
    # 核心逻辑：让球=实际结果+让球数，如果竞彩预测主胜，让球预测不可能是客胜
    # step5让球同赔只影响信心度，不改变方向
    rq_direction = ''
    rq_confidence = 0
    rq_total = 0
    rq_wins = 0
    rq_draws = 0
    rq_losses = 0
    s5_text = ''

    # 读取step5让球同赔数据
    G2_step5 = os.path.join(G2, 'step5_handicap_same.txt')
    if not os.path.exists(G2_step5):
        G2_step5 = os.path.join(G2, 'step05_handicap_same.md')
    if os.path.exists(G2_step5):
        with open(G2_step5, 'r', encoding='utf-8', errors='replace') as f:
            s5_text = f.read()
        rq_matches = re.findall(r'胜(\d+)\s+平(\d+)\s+负(\d+)', s5_text)
        if len(rq_matches) >= 2:
            # 同联赛（高权重3x） + 所有赛事（权重1x）
            sl_w, sl_d, sl_l = int(rq_matches[0][0]), int(rq_matches[0][1]), int(rq_matches[0][2])
            al_w, al_d, al_l = int(rq_matches[1][0]), int(rq_matches[1][1]), int(rq_matches[1][2])
            W = 3  # 同联赛权重
            rq_wins = sl_w * W + al_w
            rq_draws = sl_d * W + al_d
            rq_losses = sl_l * W + al_l
            rq_total = rq_wins + rq_draws + rq_losses
        else:
            rq_match = re.search(r'胜(\d+)\s+平(\d+)\s+负(\d+)', s5_text)
            if rq_match:
                rq_wins = int(rq_match.group(1))
                rq_draws = int(rq_match.group(2))
                rq_losses = int(rq_match.group(3))
                rq_total = rq_wins + rq_draws + rq_losses

    # 读取meta.json获取让球数
    rq_handicap = ''
    meta_path = os.path.join(MD, 'meta.json')
    rq = ''
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta_data = json.loads(f.read())
        rq = meta_data.get('rq', '')
    # 后备：从step5读取让球数
    if not rq and s5_text:
        rq5_match = re.search(r'让球数[：:]\s*([+-]?\d+)', s5_text)
        if rq5_match:
            rq = rq5_match.group(1)
    # 后备：从step4读取让球数
    if not rq:
        step4_file = os.path.join(G2, 'step04_handicap_basic.md')
        if os.path.exists(step4_file):
            with open(step4_file, 'r', encoding='utf-8', errors='replace') as f:
                s4_text = f.read()
            rq4_match = re.search(r'竞彩官方\s*\|\s*([+-]?\d+(?:\.\d+)?)\s*\|', s4_text)
            if rq4_match:
                rq = rq4_match.group(1)
    if rq:
        try:
            rq_val = int(float(rq))
            # meta.json中rq>0表示主队受让，rq<0表示主队让球
            if rq_val > 0:
                rq_handicap = '受让{}球 '.format(rq_val)
            elif rq_val < 0:
                rq_handicap = '让{}球 '.format(abs(rq_val))
            else:
                rq_handicap = '平手 '
        except:
            log.warn(f"[final_concl] 解析异常")
    # ============ 让球预测独立分析（多维度比分信号） ============
    # 从同联赛、亚盘、百家、主客队历史等维度提取比分信号
    rq_score_home = 0  # 主胜信号
    rq_score_draw = 0  # 平局信号
    rq_score_away = 0  # 客胜信号
    rq_score_sources = 0  # 有效数据源数量

    # 1. 同联赛统计(step8) - 有历史比分
    if s8:
        wins = s8.count('胜')
        draws = s8.count('平')
        losses = s8.count('负')
        if wins + draws + losses > 3:
            rq_score_home += wins
            rq_score_draw += draws
            rq_score_away += losses
            rq_score_sources += 1

    # 2. 主队历史(step9_13)
    if s9_13:
        wins = s9_13.count('胜')
        draws = s9_13.count('平')
        losses = s9_13.count('负')
        if wins + draws + losses > 1:
            rq_score_home += wins
            rq_score_draw += draws
            rq_score_away += losses
            rq_score_sources += 1

    # 3. 客队历史(step14_18)
    if s14_18:
        wins = s14_18.count('胜')
        draws = s14_18.count('平')
        losses = s14_18.count('负')
        if wins + draws + losses > 1:
            rq_score_home += wins
            rq_score_draw += draws
            rq_score_away += losses
            rq_score_sources += 1

    # 4. 百家对比(step19)
    if s19_23:
        home_signals = s19_23.count('主胜')
        away_signals = s19_23.count('客胜')
        draw_signals = s19_23.count('平')
        if home_signals + away_signals + draw_signals > 0:
            rq_score_home += home_signals
            rq_score_draw += draw_signals
            rq_score_away += away_signals
            rq_score_sources += 1

    # 5. 亚盘同赔(step7)
    if s7:
        wins = s7.count('胜')
        draws = s7.count('平')
        losses = s7.count('负')
        if wins + draws + losses > 2:
            rq_score_home += wins
            rq_score_draw += draws
            rq_score_away += losses
            rq_score_sources += 1

    # 综合多维度比分信号，得出独立让球预测方向
    rq_independent_direction = ''
    rq_total_score = rq_score_home + rq_score_draw + rq_score_away
    if rq_total_score > 0 and rq_score_sources >= 2:
        rq_home_rate = rq_score_home / rq_total_score
        rq_draw_rate_indep = rq_score_draw / rq_total_score
        rq_away_rate = rq_score_away / rq_total_score
        if rq_home_rate > rq_draw_rate_indep and rq_home_rate > rq_away_rate:
            rq_independent_direction = '主胜'
        elif rq_away_rate > rq_draw_rate_indep and rq_away_rate > rq_home_rate:
            rq_independent_direction = '客胜'
        elif rq_draw_rate_indep > 0.35:
            rq_independent_direction = '平局'

    # 让球预测方向：优先使用独立分析结果，否则跟随竞彩方向
    rq_pred_direction = rq_independent_direction if rq_independent_direction else direction

    # 竞彩平局 + 非零让球 → 让球结果一定不是平！
    # 竞彩主胜 + 让N球 → 让球主胜或平
    # 竞彩主胜 + 受让N球 → 让球主胜
    # 竞彩客胜 + 让N球 → 让球客胜或平
    # 竞彩客胜 + 受让N球 → 让球客胜
    # 竞彩平局 + 让N球 → 让球客胜（因为让球后主队-1，实际平局→让球后客胜）
    # 竞彩平局 + 受让N球 → 让球主胜（因为让球后主队+1，实际平局→让球后主胜）
    rq_handicap_num = 0
    if rq:
        try:
            rq_handicap_num = int(float(rq))
        except:

            log.warn(f"[final_concl] 解析异常")
    if rq_handicap_num == 0:
        # 平手盘，让球预测 = 竞彩预测
        rq_direction_final = rq_pred_direction
    elif rq_pred_direction == '平局' and rq_handicap_num != 0:
        # 竞彩平局 + 非零让球 → 让球结果一定是主胜或客胜
        if rq_handicap_num < 0:
            # 让N球（主队让球），平局→让球后客胜
            rq_direction_final = '客胜'
        else:
            # 受让N球（主队受让），平局→让球后主胜
            rq_direction_final = '主胜'
    elif rq_pred_direction == '主胜' and rq_handicap_num > 0:
        # 竞彩主胜 + 受让N球 → 让球主胜
        rq_direction_final = '主胜'
    elif rq_pred_direction == '客胜' and rq_handicap_num < 0:
        # 竞彩客胜 + 让N球 → 让球客胜
        rq_direction_final = '客胜'
    elif rq_pred_direction == '主胜':
        # 竞彩主胜 + 让N球 → 让球主胜
        rq_direction_final = '主胜'
    elif rq_pred_direction == '客胜':
        # 竞彩客胜 + 受让N球 → 让球客胜
        rq_direction_final = '客胜'
    else:
        rq_direction_final = rq_pred_direction

    # 构建让球预测文本
    if rq_direction_final == '主胜':
        rq_direction = '{}让球主胜'.format(rq_handicap) if rq_handicap else '让球主胜'
    elif rq_direction_final == '客胜':
        rq_direction = '{}让球客胜'.format(rq_handicap) if rq_handicap else '让球客胜'
    else:
        rq_direction = '{}让球平'.format(rq_handicap) if rq_handicap else '让球平'

    # ====== 让球支持率：双层加权（联赛缓存x0.7 + 让球同赔x0.3）=======
    rq_display = rq_direction

    # --- 第一层：从联赛缓存计算同联赛让球支持率（去重后） ---
    rq_cache_wins = rq_cache_draws = rq_cache_losses = rq_cache_total = 0
    rq_cache_note = ''

    if current_league and rq_handicap_num != 0:

        # 读取step5同联赛FID列表（去重用）
        s5_fids = set()
        s5_fids_path = os.path.join(G2, 'step05_same_league_fids.json')
        if os.path.exists(s5_fids_path):
            try:
                with open(s5_fids_path, 'r') as f:
                    s5_data = json.load(f)
                    s5_fids = set(s5_data.get('fids', []))
            except:
                pass

        # 读取富集联赛缓存
        cache_path = os.path.join(SCRIPT_DIR, 'data', 'league_cache', current_league + '.json')
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                matches_cache = cache_data.get('all_matches', [])

                # 获取今日欧赔初盘（从step1）
                today_iw = today_id = today_il = 0
                step1_file = os.path.join(G1, 'step1_europe_base.txt')
                if not os.path.exists(step1_file):
                    step1_file = os.path.join(G1, 'step01_europe_basic.md')
                if os.path.exists(step1_file):
                    with open(step1_file, 'r', encoding='utf-8', errors='replace') as f:
                        s1_text = f.read()
                    jc_match = re.search(r'竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', s1_text)
                    if jc_match:
                        today_iw = float(jc_match.group(1))
                        today_id = float(jc_match.group(2))
                        today_il = float(jc_match.group(3))

                if today_iw > 0:
                    rq_hl = float(rq) if rq else 0
                    for m in matches_cache:
                        fid = str(m.get('FIXTUREID', ''))
                        if not fid or fid in s5_fids:
                            continue  # 去重
                        computed = m.get('_computed')
                        if not computed:
                            continue
                        letball_res = computed.get('letball_result')
                        if not letball_res:
                            continue

                        # 条件1：近似让球 |HL - 今日HL| <= 0.5
                        hist_hl = m.get('HANDICAPLINE')
                        try:
                            hist_hl = float(hist_hl) if hist_hl else 0
                        except:
                            continue
                        if abs(hist_hl - rq_hl) > 0.5:
                            continue

                        # 条件2：指数相近（历史终盘 vs 今日初盘 偏差<10% 至少2项）
                        hist_w = m.get('WIN')
                        hist_d = m.get('DRAW')
                        hist_l = m.get('LOST')
                        try:
                            hist_w = float(hist_w) if hist_w else 0
                            hist_d = float(hist_d) if hist_d else 0
                            hist_l = float(hist_l) if hist_l else 0
                        except:
                            continue
                        if hist_w == 0:
                            continue
                        close_count = 0
                        if abs(hist_w - today_iw) / today_iw < 0.10:
                            close_count += 1
                        if abs(hist_d - today_id) / today_id < 0.10:
                            close_count += 1
                        if abs(hist_l - today_il) / today_il < 0.10:
                            close_count += 1
                        if close_count < 2:
                            continue  # 不足2项相近

                        # 统计让球结果
                        if letball_res == '主胜':
                            rq_cache_wins += 1
                        elif letball_res == '平局':
                            rq_cache_draws += 1
                        elif letball_res == '客胜':
                            rq_cache_losses += 1

                    rq_cache_total = rq_cache_wins + rq_cache_draws + rq_cache_losses
                    if rq_cache_total > 0:
                        log.info('[RQCACHE] {}让球: 胜{}平{}负{}(共{}场)'.format(                        current_league, rq_cache_wins, rq_cache_draws, rq_cache_losses, rq_cache_total))
            except Exception as e:
                log.warn('[RQCACHE] 联赛缓存读取失败: {}'.format(e))

    # --- 第二层：让球同赔数据（原有逻辑，已在前面计算好） ---
    # rq_total, rq_wins, rq_draws, rq_losses 已从step5提取

    # --- 合成最终信心度 ---
    # 权重：联赛缓存历史 0.7，让球同赔 0.3
    rq_final_wins = rq_cache_wins * 0.7 + rq_wins * 0.3
    rq_final_draws = rq_cache_draws * 0.7 + rq_draws * 0.3
    rq_final_losses = rq_cache_losses * 0.7 + rq_losses * 0.3
    rq_final_total = rq_final_wins + rq_final_draws + rq_final_losses

    rq_confidence = 0

    if rq_final_total > 0:
        rq_win_rate = rq_final_wins / rq_final_total
        rq_draw_rate = rq_final_draws / rq_final_total
        rq_loss_rate = rq_final_losses / rq_final_total

        if rq_direction_final == '主胜':
            rq_confidence = rq_win_rate
        elif rq_direction_final == '客胜':
            rq_confidence = rq_loss_rate
        else:
            rq_confidence = rq_draw_rate

        # 注释来源
        cache_count = rq_cache_total
        s5_count = rq_total
        if cache_count > 0 and s5_count > 0:
            rq_cache_note = '(联赛{}场+同赔{}场)'.format(cache_count, s5_count)
        elif cache_count > 0:
            rq_cache_note = '(联赛{}场)'.format(cache_count)
        elif s5_count > 0:
            rq_cache_note = '(同赔{}场)'.format(s5_count)

        if rq_confidence < 0.15:
            rq_display = '{}(信心不足){}'.format(rq_direction, rq_cache_note)
        else:
            rq_display = '{}{}'.format(rq_direction, rq_cache_note)

        # 折扣：方向不一致时降低信心
        if rq_direction_final == '主胜' and rq_loss_rate > rq_win_rate:
            rq_confidence = min(rq_confidence, 1 - rq_loss_rate)
        elif rq_direction_final == '客胜' and rq_win_rate > rq_loss_rate:
            rq_confidence = min(rq_confidence, 1 - rq_win_rate)
        elif rq_direction_final == '平局' and rq_draw_rate < 0.35:
            rq_confidence = min(rq_confidence, rq_draw_rate + 0.2)
    else:
        # 没有任何数据，用综合信号推断
        rq_confidence = 0.35 if abs(final_score) < 0.2 else 0.45
        rq_display = '{}(数据不足，仅供参考)'.format(rq_direction)
    # 让球预测备注：如果独立分析与竞彩方向不同，标注
    rq_direction_note = ''
    if rq_independent_direction and rq_independent_direction != direction:
        rq_direction_note = f'(独立分析指向{rq_independent_direction}，与竞彩方向不同)'

    # 生成依据列表
    evidence = []
    for name, score, weight in base_weights:
        if abs(score) > 0.1:
            trend = '利好主' if score > 0 else '利好客'
            evidence.append(f'{name}: {trend}（分值{score:+.2f}）')

    # 风险提示
    risks = []
    if total_samples < 10:
        risks.append('历史样本不足（<10场）')
    if active_dims < 5:
        risks.append('有效维度较少（<5个）')
    if data_quality < 0.4:
        risks.append('数据质量较低')
    if zhuangjia['bet_diff'] > 20:
        risks.append('投注占比差异大，存在热度')
    if jc_same['total'] < 3 and abs_score < 0.3:
        risks.append('同赔样本不足')

    # 高准确率组合提示
    high_combo_tips = []
    for combo in patterns.get('high_accuracy_combos', [])[:2]:
        high_combo_tips.append(f"{combo.get('name') or combo.get('tag', '')}（历史{combo['accuracy']*100:.0f}%）")

    # ============ Output ============
    output = []
    output.append('## 最终预测分析（V2 - 多维度组合）')
    output.append('')
    output.append('| 维度 | 结果 |')
    output.append('|------|------|')
    output.append(f'| **竞彩预测** | {direction}（信心{confidence_pct}% {confidence_level}信号） |')
    output.append(f'| **让球预测** | {rq_display}{rq_direction_note}（信心{int(rq_confidence*100)}%） |')
    output.append(f'| **信心** | {confidence_pct}%（{confidence_level}信号） |')
    output.append(f'| **综合分值** | {final_score:+.3f}（+利好主 / -利好客） |')
    output.append(f'| **数据质量** | {data_quality:.2f}（样本{total_samples}场/{active_dims}维度） |')
    output.append('')
    output.append('### 分析依据')
    output.append('')
    for i, ev in enumerate(evidence[:8], 1):
        output.append(f'{i}. {ev}')
    output.append('')
    output.append('### 欧赔盘路组合')
    output.append('')
    output.append(f'- 让球同赔：{rq_same["total"]}场 胜率{rq_same["win_rate"]:.0f}%')
    output.append(f'- 竞彩同赔：{jc_same["total"]}场 胜率{jc_same["win_rate"]:.0f}%')
    output.append(f'- IW同赔：{iw_same["total"]}场 胜率{iw_same["win_rate"]:.0f}%')
    output.append('')
    output.append('### 投注占比分析')
    output.append('')
    if zhuangjia['data']:
        output.append(f'- 主胜投注：{zhuangjia["bet_pcts"]["home"]:.1f}%（{zhuangjia["data"].get("主胜", {}).get("bet_pct", "-")}）')
        output.append(f'- 平局投注：{zhuangjia["bet_pcts"]["draw"]:.1f}%（{zhuangjia["data"].get("平局", {}).get("bet_pct", "-")}）')
        output.append(f'- 客胜投注：{zhuangjia["bet_pcts"]["away"]:.1f}%（{zhuangjia["data"].get("客胜", {}).get("bet_pct", "-")}）')
        output.append(f'- 投注差值：{zhuangjia["bet_diff"]:.1f}%')
        output.append(f'- 庄家盈亏：主{zhuangjia["profits"]["home"]:.0f} / 平{zhuangjia["profits"]["draw"]:.0f} / 客{zhuangjia["profits"]["away"]:.0f}')

        # 显示历史模式
        if patterns.get('betting_patterns'):
            output.append('')
            output.append('### 历史投注模式（从反馈数据学习）')
            output.append('')
            for bucket, stats in patterns['betting_patterns'].items():
                if stats['total'] > 0:
                    output.append(f'- 投注差值 {bucket}: {stats["total"]}场')

        # 显示联赛准确率
        if patterns.get('league_accuracy'):
            output.append('')
            output.append('### 联赛历史准确率')
            output.append('')
            leagues = patterns['league_accuracy']
            for league, stats in sorted(leagues.items(), key=lambda x: x[1].get('correct',0)/max(x[1].get('total',1),1), reverse=True)[:5]:
                total = stats.get('total', 0)
                correct = stats.get('correct', 0)
                if total >= 3:
                    acc = correct / total * 100
                    output.append(f'- {league}: {acc:.0f}% ({correct}/{total})')

        # 显示信心度准确率
        if patterns.get('confidence_accuracy'):
            output.append('')
            output.append('### 信心度历史准确率')
            output.append('')
            conf = patterns['confidence_accuracy']
            # Group by level
            high_conf = {k: v for k, v in conf.items() if '强' in k and v.get('total', 0) >= 3}
            med_conf = {k: v for k, v in conf.items() if '中' in k and v.get('total', 0) >= 3}
            low_conf = {k: v for k, v in conf.items() if '弱' in k or '回避' in k}

            if high_conf:
                total_h = sum(v['total'] for v in high_conf.values())
                correct_h = sum(v['correct'] for v in high_conf.values())
                output.append(f'- 强信号: {correct_h/total_h*100:.0f}% ({correct_h}/{total_h})')
            if med_conf:
                total_m = sum(v['total'] for v in med_conf.values())
                correct_m = sum(v['correct'] for v in med_conf.values())
                output.append(f'- 中信号: {correct_m/total_m*100:.0f}% ({correct_m}/{total_m})')
            if low_conf:
                total_l = sum(v['total'] for v in low_conf.values())
                correct_l = sum(v['correct'] for v in low_conf.values())
                output.append(f'- 弱信号: {correct_l/total_l*100:.0f}% ({correct_l}/{total_l})')

        # 显示让球预测准确率
        if patterns.get('handicap_accuracy'):
            rq = patterns['handicap_accuracy']
            if rq.get('total', 0) > 0:
                acc = rq['correct'] / rq['total'] * 100
                output.append('')
                output.append('### 让球预测历史准确率')
                output.append('')
                output.append(f'- {acc:.0f}% ({rq["correct"]}/{rq["total"]})')
    else:
        output.append('- 数据不足')
    output.append('')
    output.append('### 风险提示')
    output.append('')
    if risks:
        for risk in risks:
            output.append(f'- {risk}')
    else:
        output.append('- 无明显风险')
    output.append('')
    if high_combo_tips:
        output.append('### 高准确率组合参考')
        output.append('')
        for tip in high_combo_tips:
            output.append(f'- {tip}')
        output.append('')
    output.append('### 各维度信号明细')
    output.append('')
    output.append('| 维度 | 分值 | 权重 |')
    output.append('|------|------|------|')
    for name, score, weight in base_weights:
        # 输出所有维度，不过滤（确保sync_notion.js能提取到所有字段）
        if True:
            trend = '利好主' if score > 0 else ('利好客' if score < 0 else '中立')
            output.append(f'| {name} | {score:+.3f} {trend} | {weight*100:.0f}% |')
    output.append('')
    output.append('---')
    output.append('')
    output.append('*提示：以上分析基于数据驱动规则引擎 + 历史模式学习，每个结论均可追溯到具体数据。投资有风险，请结合实战判断。*')

        # Step26由step25_zhuangjia.py生成，此处不重复写入


    return '\n'.join(output)
if __name__ == "__main__":
    md = _sys.argv[1] if len(_sys.argv) > 1 else ""
    if md and os.path.isdir(md):
        text = generate_conclusion(md)
        print(text)
    else:
        print("Usage: python final_conclusion_generator.py <match_dir>")
