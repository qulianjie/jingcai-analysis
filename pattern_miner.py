# -*- coding: utf-8 -*-
"""
竞彩历史模式挖掘器 V1 - 多维特征交叉 + 关联规则发现
"""

import os, sys, json, itertools
from datetime import datetime
from collections import Counter, defaultdict

# 周期检测引擎
try:
    from periodicity import build_combo_sequences, print_periodic_patterns
    HAS_PERIODICITY = True
except ImportError:
    HAS_PERIODICITY = False
    def build_combo_sequences(matches): return {}
    def print_periodic_patterns(s, top=20): pass

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _util import rd, safe_json_load, ensure_utf8_stdout
    ensure_utf8_stdout()
except ImportError:
    def rd(path):
        try: return open(path, 'r', encoding='utf-8').read()
        except: return ''

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
PATTERNS_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'historical_patterns.json')


def discretize_pct(val_str):
    try:
        v = float(str(val_str).replace('%', '').replace(',', ''))
        if v >= 45: return '高'
        if v >= 30: return '中'
        return '低'
    except: return ''


def discretize_pr(v):
    try:
        v = float(v)
        if v >= 0.4: return '高'
        if v >= 0.2: return '中'
        return '低'
    except: return ''


def extract_features(item):
    """从反馈条目提取所有可用特征（含赔率衍生）"""
    f = {}
    c = item.get('combos', {})
    s25 = item.get('s25', {})
    s26 = item.get('s26', {})

    # 盘路特征
    for k in ['竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路']:
        v = c.get(k, '')
        if v: f[k] = v

    # 方向特征
    dm = {
        '欧赔趋势_dir': '欧赔方向', '亚盘趋势_dir': '亚盘方向',
        '让球趋势_dir': '让球方向', '百家对比_dir': '百家方向',
        '盘路匹配_dir': '盘路匹配方向', '庄家盈亏_dir': '庄家盈亏方向',
    }
    for src, dst in dm.items():
        v = c.get(src, '')
        if v: f[dst] = v

    # 盘路匹配度
    pm = c.get('盘路匹配', '')
    if pm: f['盘路匹配度'] = pm

    # 澳门亚盘（保留原始盘口值，如"平手/半球""受平手/半球""半球"）
    macau = c.get('澳门亚盘', '')
    if macau and macau != '未知':
        f['澳门亚盘'] = macau

    # 庄家盈亏
    for r in ['主胜', '平局', '客胜']:
        v = s25.get(r + '_盈亏', '')
        if v: f['庄家' + r + '盈亏'] = '赢' if '赢' in str(v) else ('亏' if '亏' in str(v) else v)

    # 投注占比
    ratios = []
    for r, s in [('主胜', '主'), ('平局', '平'), ('客胜', '客')]:
        v = s25.get(r + '_占比', '')
        if v:
            bucket = discretize_pct(v)
            f['投注占比_' + s] = bucket
            ratios.append(bucket)
    if len(ratios) == 3 and '' not in ratios:
        f['投注占比三段'] = '/'.join(ratios)

    # ===== 赔率衍生特征（竞彩/IW/百家） =====
    for prefix, tag in [
        ('欧赔', 'JC'), ('IW', 'IW'), ('百家', 'BJ')
    ]:
        s = c.get(prefix + '初胜', None)
        p = c.get(prefix + '初平', None)
        fu = c.get(prefix + '初负', None)
        si = c.get(prefix + '即胜', None)
        pi = c.get(prefix + '即平', None)
        fui = c.get(prefix + '即负', None)
        if s is None or p is None or fu is None:
            continue
        try:
            sv, pv, fv = float(s), float(p), float(fu)
        except:
            continue

        # 初盘特征
        if sv <= 1.6: f[tag + '初胜赔'] = '低'
        elif sv <= 2.5: f[tag + '初胜赔'] = '中'
        else: f[tag + '初胜赔'] = '高'
        diff = abs(sv - fv)
        if diff <= 0.5: f[tag + '初胜负差'] = '小'
        elif diff <= 1.5: f[tag + '初胜负差'] = '中'
        else: f[tag + '初胜负差'] = '大'
        f[tag + '初平赔高'] = '是' if (pv > sv and pv > fv) else '否'
        if sv < pv < fv: f[tag + '初形态'] = '顺分布'
        elif sv > pv > fv: f[tag + '初形态'] = '逆分布'
        elif pv > sv and pv > fv: f[tag + '初形态'] = '平赔最高'
        elif sv < fv: f[tag + '初形态'] = '主优'
        else: f[tag + '初形态'] = '客优'

        # 即时盘特征
        if si is None or pi is None or fui is None:
            continue
        try:
            siv, piv, fiv = float(si), float(pi), float(fui)
        except:
            continue
        if siv <= 1.6: f[tag + '即胜赔'] = '低'
        elif siv <= 2.5: f[tag + '即胜赔'] = '中'
        else: f[tag + '即胜赔'] = '高'
        diff2 = abs(siv - fiv)
        if diff2 <= 0.5: f[tag + '即胜负差'] = '小'
        elif diff2 <= 1.5: f[tag + '即胜负差'] = '中'
        else: f[tag + '即胜负差'] = '大'
        f[tag + '即平赔高'] = '是' if (piv > siv and piv > fiv) else '否'
        if siv < piv < fiv: f[tag + '即形态'] = '顺分布'
        elif siv > piv > fiv: f[tag + '即形态'] = '逆分布'
        elif piv > siv and piv > fiv: f[tag + '即形态'] = '平赔最高'
        elif siv < fiv: f[tag + '即形态'] = '主优'
        else: f[tag + '即形态'] = '客优'
        f[tag + '即胜赔_raw'] = str(round(siv, 1))
        f[tag + '即胜负差_raw'] = str(round(siv - fiv, 1))
        # 原始值（保留1位小数，用于精确匹配）
        f[tag + '即胜赔_raw'] = str(round(siv, 1))
        diff_signed = round(siv - fiv, 1)
        f[tag + '即胜负差_raw'] = str(diff_signed)

    # ===== 让球指数特征（完整版：赔率分段+盘路变化+形态） =====
    for prefix, tag in [('让球', 'RQ')]:
        s = c.get(prefix + '初胜', None)
        p = c.get(prefix + '初平', None)
        fu = c.get(prefix + '初负', None)
        si = c.get(prefix + '即胜', None)
        pi = c.get(prefix + '即平', None)
        fui = c.get(prefix + '即负', None)

        if s is not None and p is not None and fu is not None:
            try:
                sv, pv, fv = float(s), float(p), float(fu)
                if sv <= 2.0: f[tag + '初胜赔'] = '低'
                elif sv <= 3.5: f[tag + '初胜赔'] = '中'
                else: f[tag + '初胜赔'] = '高'
                if pv <= 2.0: f[tag + '初平赔'] = '低'
                elif pv <= 3.5: f[tag + '初平赔'] = '中'
                else: f[tag + '初平赔'] = '高'
                if fv <= 2.0: f[tag + '初负赔'] = '低'
                elif fv <= 3.5: f[tag + '初负赔'] = '中'
                else: f[tag + '初负赔'] = '高'
                diff_rq = abs(sv - fv)
                if diff_rq <= 0.5: f[tag + '初胜负差'] = '小'
                elif diff_rq <= 1.5: f[tag + '初胜负差'] = '中'
                else: f[tag + '初胜负差'] = '大'
                f[tag + '初平赔高'] = '是' if (pv > sv and pv > fv) else '否'
                if sv < pv < fv: f[tag + '初形态'] = '顺分布'
                elif sv > pv > fv: f[tag + '初形态'] = '逆分布'
                elif pv > sv and pv > fv: f[tag + '初形态'] = '平赔最高'
                elif sv < fv: f[tag + '初形态'] = '主优'
                else: f[tag + '初形态'] = '客优'
            except: pass
        if si is not None and pi is not None and fui is not None:
            try:
                siv, piv, fiv = float(si), float(pi), float(fui)
                if siv <= 2.0: f[tag + '即胜赔'] = '低'
                elif siv <= 3.5: f[tag + '即胜赔'] = '中'
                else: f[tag + '即胜赔'] = '高'
                if piv <= 2.0: f[tag + '即平赔'] = '低'
                elif piv <= 3.5: f[tag + '即平赔'] = '中'
                else: f[tag + '即平赔'] = '高'
                if fiv <= 2.0: f[tag + '即负赔'] = '低'
                elif fiv <= 3.5: f[tag + '即负赔'] = '中'
                else: f[tag + '即负赔'] = '高'
                diff2_rq = abs(siv - fiv)
                if diff2_rq <= 0.5: f[tag + '即胜负差'] = '小'
                elif diff2_rq <= 1.5: f[tag + '即胜负差'] = '中'
                else: f[tag + '即胜负差'] = '大'
                f[tag + '即平赔高'] = '是' if (piv > siv and piv > fiv) else '否'
                if siv < piv < fiv: f[tag + '即形态'] = '顺分布'
                elif siv > piv > fiv: f[tag + '即形态'] = '逆分布'
                elif piv > siv and piv > fiv: f[tag + '即形态'] = '平赔最高'
                elif siv < fiv: f[tag + '即形态'] = '主优'
                else: f[tag + '即形态'] = '客优'
            except: pass

        # 让球数
        rq = c.get('让球数', '')
        if rq: f['让球数'] = rq
        # 让球盘路变化
        rq_trend = c.get('让球盘路_基准', '')
        if rq_trend: f['让球盘路'] = rq_trend

    # 盈亏占比
    for r in ['主', '平', '客']:
        v = s26.get('盈亏占比_' + r, '')
        if v != '' and v is not None:
            bucket = discretize_pr(v)
            if bucket: f['盈亏占比_' + r] = bucket

    # 庄家胜平负盈亏方向
    for r in ['胜', '平', '负']:
        v = s26.get('庄家' + r + '盈亏_方向', '')
        if v: f['庄家' + r + '盈亏_方向'] = v

    # 综合盈亏方向
    v = s26.get('综合盈亏方向', '')
    if v: f['综合盈亏方向'] = v

    # 大热方
    v = s25.get('大热方', '')
    if v: f['大热方'] = v

    # 联赛
    league = item.get('league', '')
    if league: f['联赛'] = league

    return f


def apriori_mine_patterns(matches, base_pct, core_dims, fv, min_lift=1.5, min_support=3):
    """Apriori算法挖掘4维+高频项集（优化版：倒排索引+维度缩减+项集上限）"""
    from collections import defaultdict

    # 缩减维度：去掉冗余赔率分段，保留高信息量维度
    important = ['竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路', '让球盘路',
                 '庄家主胜盈亏', '庄家平局盈亏', '庄家客胜盈亏',
                 '大热方', '澳门亚盘', '联赛',
                 'JC即胜赔_raw', 'JC即胜负差_raw',
                 'RQ即负赔_raw', 'RQ即胜负差_raw']
    dims = [d for d in important if d in core_dims or d in fv]
    print('[Apriori] 使用 %d 个维度' % len(dims))

    # 构建倒排索引：item -> set(match_idx)
    inv = defaultdict(set)
    transactions = []
    actuals = []
    for i, m in enumerate(matches):
        items = set()
        for d in dims:
            v = m['features'].get(d)
            if v:
                item = d + '=' + v
                items.add(item)
                inv[item].add(i)
        transactions.append(items)
        actuals.append(m.get('actual', ''))

    # 1项集
    freq = {1: []}
    freq_set = {1: set()}
    for item, idxs in inv.items():
        if len(idxs) >= min_support:
            fs = frozenset([item])
            freq[1].append(fs)
            freq_set[1].add(fs)
    print('[Apriori] 1项集: %d' % len(freq[1]))

    MAX_CAP = 50000  # k项集数量上限

    for k in range(2, 9):
        if not freq[k-1] or len(freq[k-1]) > MAX_CAP:
            if len(freq[k-1]) > MAX_CAP:
                print('[Apriori] %d项集数量 %d > 上限 %d，终止扩展' % (k-1, len(freq[k-1]), MAX_CAP))
            break

        candidates = set()
        f_list = list(freq[k-1])
        f_set_kminus1 = freq_set[k-1]

        if k == 2:
            dim_items = defaultdict(list)
            for fs in f_list:
                item = list(fs)[0]
                dim = item.split('=', 1)[0]
                dim_items[dim].append(item)
            dims_list = list(dim_items.keys())
            for i in range(len(dims_list)):
                for j in range(i+1, len(dims_list)):
                    for va in dim_items[dims_list[i]]:
                        for vb in dim_items[dims_list[j]]:
                            candidates.add(frozenset([va, vb]))
        else:
            groups = defaultdict(list)
            for fs in f_list:
                sorted_items = sorted(fs)
                key = tuple(sorted_items[:-1])
                groups[key].append(sorted_items[-1])
            for prefix, tails in groups.items():
                if len(tails) < 2:
                    continue
                for i in range(len(tails)):
                    for j in range(i+1, len(tails)):
                        dim_a = tails[i].split('=', 1)[0]
                        dim_b = tails[j].split('=', 1)[0]
                        if dim_a == dim_b:
                            continue
                        cand = frozenset(list(prefix) + [tails[i], tails[j]])
                        # 剪枝：所有(k-1)子集必须存在
                        valid = True
                        from itertools import combinations as _comb
                        for subset in _comb(sorted(cand), k-1):
                            if frozenset(subset) not in f_set_kminus1:
                                valid = False
                                break
                        if valid:
                            candidates.add(cand)

        # 用倒排索引快速计数
        freq_k = []
        freq_k_set = set()
        for cand in candidates:
            # 取交集
            idx_iter = None
            for item in cand:
                if idx_iter is None:
                    idx_iter = set(inv.get(item, set()))
                else:
                    idx_iter &= inv.get(item, set())
                if len(idx_iter) < min_support:
                    break
            if idx_iter and len(idx_iter) >= min_support:
                freq_k.append(cand)
                freq_k_set.add(cand)
        freq[k] = freq_k
        freq_set[k] = freq_k_set
        print('[Apriori] %d项集: %d' % (k, len(freq_k)))

    # 从4维+提取模式
    patterns = []
    for dim_n in range(4, k):
        for itemset in freq.get(dim_n, []):
            # 用倒排索引取交集
            idx_iter = None
            for item in itemset:
                if idx_iter is None:
                    idx_iter = set(inv.get(item, set()))
                else:
                    idx_iter &= inv.get(item, set())
            if not idx_iter or len(idx_iter) < min_support:
                continue

            oc = Counter()
            for i in idx_iter:
                oc[actuals[i]] += 1
            total = sum(oc.values())
            if total < min_support:
                continue

            combo = {}
            for item in itemset:
                d, v = item.split('=', 1)
                combo[d] = v
            for result, count in oc.items():
                pct = count / total
                bp = base_pct.get(result, 0.01)
                lift = pct / bp if bp > 0 else 999
                if lift >= min_lift:
                    patterns.append({
                        'combo': combo,
                        'result': result,
                        'pct': pct,
                        'lift': lift,
                        'total': total,
                        'correct': count,
                        'outcomes': dict(oc),
                        'dim_n': dim_n,
                        'source': 'apriori',
                        'sample': '',
                    })
    print('[Apriori] 4+维有效模式: %d' % len(patterns))
    l2 = len([p for p in patterns if p['lift'] >= 2.0])
    l3 = len([p for p in patterns if p['lift'] >= 3.0])
    if patterns:
        print('[Apriori] lift>=2: %d, >=3: %d' % (l2, l3))
    return patterns


def build_patterns(feedback, min_lift=1.5):
    dates = feedback.get('dates', {})
    matches = []
    for date, v in dates.items():
        for item in v.get('feedback', []):
            actual = item.get('actual', '')
            if actual not in ('胜', '平', '负'): continue
            feat = extract_features(item)
            if feat:
                matches.append({
                    'features': feat, 'actual': actual,
                    'match_num': item.get('match_num', ''),
                    'date': date,
                })

    total = len(matches)
    print('[模式挖掘] 共 %d 场比赛' % total)
    if total == 0:
        print('[模式挖掘] ⚠️ 无比赛数据，跳过模式挖掘')
        return [], {}, []
    base_ct = Counter(m['actual'] for m in matches)
    base_pct = {k: v / total for k, v in base_ct.items()}
    print('[模式挖掘] 基础概率: 胜=%.1f%% 平=%.1f%% 负=%.1f%%' % (
        base_pct.get('胜', 0)*100, base_pct.get('平', 0)*100, base_pct.get('负', 0)*100))

    fv = defaultdict(set)
    for m in matches:
        for k, v in m['features'].items():
            if v: fv[k].add(v)

    dims = ['竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路',
            '欧赔方向', '亚盘方向', '让球方向', '百家方向',
            '盘路匹配方向', '庄家盈亏方向', '盘路匹配度',
            '澳门亚盘',
            '庄家主胜盈亏', '庄家平局盈亏', '庄家客胜盈亏',
            '投注占比_主', '投注占比_平', '投注占比_客',
            '投注占比三段', '盈亏占比_主', '盈亏占比_平', '盈亏占比_客',
            '庄家胜盈亏_方向', '庄家平盈亏_方向', '庄家负盈亏_方向',
            '综合盈亏方向', '大热方', '联赛',
            'JC初胜赔', 'JC初胜负差', 'JC初平赔高', 'JC初形态',
            'JC即胜赔', 'JC即胜负差', 'JC即平赔高', 'JC即形态',
            'IW初胜赔', 'IW初胜负差', 'IW初平赔高', 'IW初形态',
            'IW即胜赔', 'IW即胜负差', 'IW即平赔高', 'IW即形态',
            'BJ初胜赔', 'BJ初胜负差', 'BJ初平赔高', 'BJ初形态',
            'BJ即胜赔', 'BJ即胜负差', 'BJ即平赔高', 'BJ即形态',
            'RQ初胜赔', 'RQ初平赔', 'RQ初负赔',
            'RQ初胜负差', 'RQ初平赔高', 'RQ初形态',
            'RQ即胜赔', 'RQ即平赔', 'RQ即负赔',
            'RQ即胜负差', 'RQ即平赔高', 'RQ即形态',
            '让球数', '让球盘路']
    dims = [d for d in dims if d in fv]

    patterns = []

    # 1维
    for dn in dims:
        for dv in fv[dn]:
            oc = Counter(); ms = []
            for m in matches:
                if m['features'].get(dn) == dv:
                    oc[m['actual']] += 1; ms.append(m)
            nt = sum(oc.values())
            if nt < 2: continue
            for result, count in oc.items():
                pct = count / nt
                bp = base_pct.get(result, 0.01)
                lift = pct / bp if bp > 0 else 999
                if lift >= min_lift:
                    patterns.append({
                        'combo': {dn: dv}, 'result': result,
                        'pct': pct, 'lift': lift, 'total': nt,
                        'correct': count, 'outcomes': dict(oc), 'dim_n': 1,
                        'sample': ms[0]['date'] + ' ' + ms[0]['match_num'],
                    })

    # 2维
    for da, db in itertools.combinations(dims, 2):
        for va in fv[da]:
            for vb in fv[db]:
                oc = Counter(); ms = []
                for m in matches:
                    if m['features'].get(da) == va and m['features'].get(db) == vb:
                        oc[m['actual']] += 1; ms.append(m)
                nt = sum(oc.values())
                if nt < 2: continue
                for result, count in oc.items():
                    pct = count / nt
                    bp = base_pct.get(result, 0.01)
                    lift = pct / bp if bp > 0 else 999
                    if lift >= min_lift:
                        patterns.append({
                            'combo': {da: va, db: vb}, 'result': result,
                            'pct': pct, 'lift': lift, 'total': nt,
                            'correct': count, 'outcomes': dict(oc), 'dim_n': 2,
                            'sample': ms[0]['date'] + ' ' + ms[0]['match_num'],
                        })

    # 3维（核心维度）
    core = ['竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路', '让球盘路',
            '庄家主胜盈亏', '庄家平局盈亏', '庄家客胜盈亏',
            '大热方',
            '澳门亚盘', '联赛',
            'JC即胜赔', 'JC即胜负差',
            'RQ即负赔', 'RQ即胜负差',
            'JC即胜赔_raw', 'JC即胜负差_raw',
            'RQ即负赔_raw', 'RQ即胜负差_raw']
    core = [d for d in core if d in fv]
    for da, db, dc in itertools.combinations(core, 3):
        for va in list(fv[da])[:5]:
            for vb in list(fv[db])[:5]:
                pre = [m for m in matches
                       if m['features'].get(da) == va
                       and m['features'].get(db) == vb]
                if len(pre) < 2: continue
                for vc in list(fv[dc])[:5]:
                    oc = Counter(); ms = []
                    for m in pre:
                        if m['features'].get(dc) == vc:
                            oc[m['actual']] += 1; ms.append(m)
                    nt = sum(oc.values())
                    if nt < 2: continue
                    best_n = max(oc.values())
                    best_r = max(oc, key=lambda k: oc[k])
                    pct = best_n / nt
                    bp = base_pct.get(best_r, 0.01)
                    lift = pct / bp if bp > 0 else 999
                    if lift >= min_lift and best_n >= 2:
                        patterns.append({
                            'combo': {da: va, db: vb, dc: vc},
                            'result': best_r, 'pct': pct, 'lift': lift,
                            'total': nt, 'correct': best_n,
                            'outcomes': dict(oc), 'dim_n': 3,
                            'sample': ms[0]['date'] + ' ' + ms[0]['match_num'],
                        })

    # 4维+ Apriori（超时保护2h，互斥锁防并发）
    import signal
    class _Lock:
        def __enter__(self):
            import platform, os
            self.lf = open(os.path.join(SCRIPT_DIR, '.pattern_miner.lock'), 'w')
            if platform.system() == 'Windows':
                import msvcrt
                msvcrt.locking(self.lf.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return self
        def __exit__(self, *a):
            import platform
            try:
                if platform.system() == 'Windows':
                    import msvcrt; msvcrt.locking(self.lf.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl; fcntl.flock(self.lf.fileno(), fcntl.LOCK_UN)
                self.lf.close()
            except: pass
    try:
        with _Lock():
            pass  # lock acquired
    except (IOError, OSError, BlockingIOError):
        print('[Apriori] 互斥锁被占用，退出（另一个pattern_miner正在运行）')
        return patterns
    
    import platform as _plat
    class TimeoutError(Exception): pass
    if _plat.system() != 'Windows':
        def _timeout_handler(sig, frame): raise TimeoutError('Apriori运行超时2h')
        signal.signal(signal.SIGALRM, _timeout_handler)
    
    print('[Apriori] 开始挖掘4维+模式（核心维度池 %d维，min_support=1(4维+)，超时2h）...' % len(core))
    try:
        apriori_pats = apriori_mine_patterns(matches, base_pct, core, fv, min_lift, min_support=1)
        patterns.extend(apriori_pats)
        if _plat.system() != 'Windows': signal.alarm(0)
    except TimeoutError:
        print('[Apriori] ⚠️ 超时2h，终止挖掘')
    except Exception as e:
        print('[Apriori] 出错: %s (内存不足或数据处理异常)' % e)
    finally:
        import platform as _p
        if _p.system() != 'Windows': signal.alarm(0)
        try: lf.close(); os.remove(LOCKFILE)
        except: pass

    # 去重
    seen = set(); uniq = []
    for p in patterns:
        ki = tuple(sorted(p['combo'].items())) + (p['result'],)
        if ki not in seen:
            seen.add(ki); uniq.append(p)
    uniq.sort(key=lambda x: (-x['lift'], -x['total']))

    # 去掉1维和2维（用户要求只保留3维+）
    uniq = [p for p in uniq if p.get('dim_n', 0) >= 2]
    print('[模式挖掘] 去掉1维后（保留2维） %d 个有效模式' % len(uniq))
    l2 = len([p for p in uniq if p['lift'] >= 2.0])
    l3 = len([p for p in uniq if p['lift'] >= 3.0])
    l5 = len([p for p in uniq if p['lift'] >= 5.0])
    print('[模式挖掘] lift>=2: %d, >=3: %d, >=5: %d' % (l2, l3, l5))
    return uniq, base_pct, matches


def print_top(patterns, base_pct, top=25):
    print('\n' + '='*60)
    print('模式挖掘结果')
    print('='*60)
    for dn in sorted(set(p['dim_n'] for p in patterns)):
        dps = [p for p in patterns if p['dim_n'] == dn]
        if not dps: continue
        tag = 'Apriori ' if dn >= 4 else ''
        print('\n--- %s%d维组合（前%d条）---' % (tag, dn, min(top, len(dps))))
        for p in dps[:top]:
            cp = ' / '.join('%s=%s' % (k, v) for k, v in sorted(p['combo'].items()))
            oc = ', '.join('%s:%d' % (k, v) for k, v in sorted(p['outcomes'].items()))
            print('  [%d维][%.0f%%][x%.1f] %s -> %s (%s)' % (
                p['dim_n'], p['pct']*100, p['lift'], cp, p['result'], oc))
            if p['total'] >= 5:
                print('    样本: %s 等%d场' % (p['sample'], p['total']))


def main():
    print('\n' + '='*60)
    print('竞彩历史模式挖掘器 V1')
    print('数据时间: %s' % datetime.now().strftime('%Y-%m-%d %H:%M'))
    print('='*60 + '\n')

    print('[1/4] 加载反馈数据...')
    raw = rd(FEEDBACK_FILE)
    if not raw:
        print('ERROR: feedback.json not found')
        return
    fb = json.loads(raw)
    print('       %d 个日期' % len(fb.get('dates', {})))

    print('[2/4] 挖掘模式...')
    patterns, base_pct, matches = build_patterns(fb, min_lift=1.5)

    print('[3/4] 输出Top模式...')
    print_top(patterns, base_pct, top=30)

    print('[3.5/4] 构建时间序列（周期检测）...')
    if HAS_PERIODICITY:
        sequences = build_combo_sequences(matches)
        periodic_count = len([v for v in sequences.values() if v.get('period', {}).get('found')])
        print('      共 %d 个组合序列，其中 %d 个有周期信号' % (len(sequences), periodic_count))
        if periodic_count > 0:
            print_periodic_patterns(sequences, top=15)
    else:
        sequences = {}
        print('      周期检测模块未加载，跳过')
    print('')

    print('[4/4] 保存模式库...')
    out = {
        'version': '1.0',
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_matches': len(matches),
        'total_patterns': len(patterns),
        'base_rates': base_pct,
        'patterns': patterns,
        'sequences': sequences,
        'summary': {
            '1d': len([p for p in patterns if p['dim_n'] == 1]),
            '2d': len([p for p in patterns if p['dim_n'] == 2]),
            '3d': len([p for p in patterns if p['dim_n'] == 3]),
            '4d+': len([p for p in patterns if p['dim_n'] >= 4]),
            'lift_ge_2': len([p for p in patterns if p['lift'] >= 2.0]),
            'lift_ge_3': len([p for p in patterns if p['lift'] >= 3.0]),
            'lift_ge_5': len([p for p in patterns if p['lift'] >= 5.0]),
        }
    }
    with open(PATTERNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('保存完成: %s' % PATTERNS_FILE)

    # 同步模式库到Notion
    try:
        sync_script = os.path.join(SCRIPT_DIR, 'sync_patterns_to_notion.py')
        if os.path.exists(sync_script):
            import subprocess
            subprocess.run(['python3', sync_script], timeout=120)
    except:
        pass


if __name__ == '__main__':
    main()