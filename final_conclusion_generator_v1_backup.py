# -*- coding: utf-8 -*-
"""
竞彩分析结论生成器 V1 - 从24步数据中提取信号 + 加权打分 + 生成结论
不依赖外部模型，纯规则引擎 + 数据驱动

用法:
    python final_conclusion_generator.py <match_dir_path>
    输出到 stdout，由 final_report_generator.py 集成调用
"""
import os, sys, re, json
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if len(sys.argv) < 2:
    print('Usage: python final_conclusion_generator.py <match_dir_path>')
    sys.exit(1)

MD = sys.argv[1]
PARENT = os.path.dirname(MD)

def rd(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

def rd_json(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def re_find(text, pattern, default=''):
    m = re.search(pattern, text)
    return m.group(1) if m else default

def re_find_float(text, pattern, default=0.0):
    v = re_find(text, pattern)
    try: return float(v)
    except: return default

# ============ Paths ============
G1 = os.path.join(MD, 'group01_europe')
G2 = os.path.join(MD, 'group02_handicap')
G3 = os.path.join(MD, 'group03_asian')
G4 = os.path.join(MD, 'group04_teamA')
G5 = os.path.join(MD, 'group05_teamB')
G6 = os.path.join(MD, 'group06_baijia')

# meta
meta_raw = rd(os.path.join(MD, 'meta.json'))
try:
    meta = json.loads(meta_raw) if meta_raw else {}
except:
    meta = {}
home_name = meta.get('home', '主队')
away_name = meta.get('away', '客队')

# ============ Read all step data ============
s1 = rd(os.path.join(G1, 'step01_europe_basic.md'))
s2 = rd(os.path.join(G1, 'step02_jingcai_same.md'))
s3 = rd(os.path.join(G1, 'step03_interwetten_same.md'))
s4 = rd(os.path.join(G2, 'step04_handicap_basic.md'))
s5 = rd(os.path.join(G2, 'step05_handicap_same.md'))
s6 = rd(os.path.join(G3, 'step06_asian_basic.md'))
s7 = rd(os.path.join(G3, 'step07_macau_same.md'))
s8 = rd(os.path.join(G3, 'step08_same_league.md'))
s9_13 = rd(os.path.join(G4, 'step09_13_teamA.md'))
s14_18 = rd(os.path.join(G5, 'step14_18_teamB.md'))
s19_23 = rd(os.path.join(G6, 'step19_23_baijia.md'))
s24 = rd(os.path.join(MD, 'step24_panlu_match.json'))
s25 = rd(os.path.join(MD, 'step25_zhuangjia.json'))
if not s25:
    s25 = rd(os.path.join(PARENT, 'step25_zhuangjia.json'))

# ============ Signal 1: 欧赔趋势（step1）============
def analyze_europe_odds(text):
    """从step1欧赔基础中提取方向信号"""
    signals = []
    # 提取竞彩初→终盘变化
    jc_change = re_find(text, r'竞彩官方.*?([\u2b07\u2b06\u27a1]{3})')
    if jc_change and len(jc_change) == 3:
        # 胜降→利好主，负降→利好客，平降→利好平
        s_score = -1 if jc_change[0] == '\u2b07' else (1 if jc_change[0] == '\u2b06' else 0)
        d_score = -1 if jc_change[1] == '\u2b07' else (1 if jc_change[1] == '\u2b06' else 0)
        l_score = -1 if jc_change[2] == '\u2b07' else (1 if jc_change[2] == '\u2b06' else 0)
        # 主胜降 = 利好主 = 负方向
        net = s_score * -1  # 胜降→-(-1)=+1(利好主)
        signals.append(('竞彩', s_score * -1 + d_score * -0.3 + l_score * -1))

    # 提取百家变化
    bj_change = re_find(text, r'百家平均.*?([\u2b07\u2b06\u27a1]{3})')
    if bj_change and len(bj_change) == 3:
        s = -1 if bj_change[0] == '\u2b07' else (1 if bj_change[0] == '\u2b06' else 0)
        l = -1 if bj_change[2] == '\u2b07' else (1 if bj_change[2] == '\u2b06' else 0)
        signals.append(('百家', s * -1 + l * -1))

    # 提取具体赔率值
    jc_odds = re_find(text, r'竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)')
    bj_odds = re_find(text, r'百家平均\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)')

    score = sum(s[1] for s in signals) / max(len(signals), 1) if signals else 0
    return {
        'score': max(-1, min(1, score)),
        'details': signals,
        'jc_odds': jc_odds,
        'bj_odds': bj_odds,
    }

# ============ Signal 2: 欧赔同赔（step2/3）============
def analyze_same_odds(text, name):
    """从同赔统计中提取方向信号"""
    total = re_find_float(text, r'共(\d+)场')
    if total < 1:
        return {'score': 0, 'total': 0, 'win_rate': 0}

    wins = int(re_find(text, r'胜(\d+)') or '0')
    draws = int(re_find(text, r'平(\d+)') or '0')
    losses = int(re_find(text, r'负(\d+)') or '0')

    # 同赔中"胜多"→利好主，"负多"→利好客
    win_rate = wins / total if total > 0 else 0
    lose_rate = losses / total if total > 0 else 0
    draw_rate = draws / total if total > 0 else 0

    # score: +1=利好主，-1=利好客
    score = (win_rate - lose_rate)
    if abs(score) < 0.1:
        score = 0

    return {
        'score': max(-1, min(1, score)),
        'total': total,
        'win_rate': win_rate,
        'draw_rate': draw_rate,
        'lose_rate': lose_rate,
        'wins': wins, 'draws': draws, 'losses': losses,
        'name': name,
    }

# ============ Signal 3: 澳门亚盘（step6/7/8）============
def analyze_macau_asian(s6_text, s7_text, s8_text):
    """从澳门亚盘+同赔+同联赛统计中提取信号"""
    signals = []

    # Step7: 澳门同赔统计
    s7_total = re_find_float(s7_text, r'共(\d+)场')
    if s7_total >= 1:
        s7_wins = int(re_find(s7_text, r'胜(\d+)') or '0')
        s7_draws = int(re_find(s7_text, r'平(\d+)') or '0')
        s7_losses = int(re_find(s7_text, r'负(\d+)') or '0')
        s7_score = (s7_wins - s7_losses) / s7_total if s7_total > 0 else 0
        signals.append(('澳门同赔', max(-1, min(1, s7_score)), int(s7_total)))

    # Step8: 同联赛同盘路统计
    s8_total = re_find_float(s8_text, r'主队赢盘率.*?\((\d+\.?\d*)场\)')
    s8_home_rate = re_find_float(s8_text, r'主队赢盘率:\s*([\d.]+)%')
    s8_away_rate = re_find_float(s8_text, r'客队赢盘率:\s*([\d.]+)%')
    if s8_home_rate > 0 or s8_away_rate > 0:
        s8_score = (s8_home_rate - s8_away_rate) / 100
        signals.append(('同联赛盘路', max(-1, min(1, s8_score)), int(s8_total) if s8_total else 0))

    # Step8: 欧赔明细（竞彩/Interwetten/百家匹配度统计）
    jc_match_score = re_find_float(s8_text, r'竞彩.*?\n高盘路:\s*胜(\d+)\s*平(\d+)\s*负(\d+)')
    jc_s = int(re_find(s8_text, r'竞彩[\s\S]*?高盘路:\s*胜(\d+)') or '0')
    jc_d = int(re_find(s8_text, r'竞彩[\s\S]*?高盘路:\s*胜\d+\s*平(\d+)') or '0')
    jc_l = int(re_find(s8_text, r'竞彩[\s\S]*?高盘路:\s*胜\d+\s*平\d+\s*负(\d+)') or '0')
    jc_total = jc_s + jc_d + jc_l
    if jc_total > 0:
        jc_net = (jc_s - jc_l) / jc_total
        signals.append(('同联赛竞彩', max(-1, min(1, jc_net)), jc_total))

    if not signals:
        return {'score': 0, 'details': []}

    # 加权：澳门同赔0.5，同联赛盘路0.3，同联赛竞彩0.2
    weights = [0.5, 0.3, 0.2]
    total_score = 0
    total_weight = 0
    detail_list = []
    for i, (name, score, count) in enumerate(signals):
        w = weights[i] if i < len(weights) else 0.1
        total_score += score * w
        total_weight += w
        detail_list.append((name, score, count))

    avg = total_score / total_weight if total_weight > 0 else 0
    return {'score': max(-1, min(1, avg)), 'details': detail_list}

# ============ Signal 4: 主队主场（step9-13）============
def analyze_home_team(text):
    """从主队主场分析提取信号"""
    home_win_rate = re_find_float(text, r'胜率\s*([\d.]+)%')
    home_cover_rate = re_find_float(text, r'赢盘率\s*([\d.]+)%')
    home_total = int(re_find(text, r'共(\d+)\s*场') or '0')

    if home_total < 1:
        return {'score': 0, 'win_rate': 0, 'cover_rate': 0, 'total': 0}

    # 胜率>50%利好主
    score = (home_win_rate - 50) / 50  # 0~100 → -1~+1

    # 盘路匹配度统计
    high_win = int(re_find(text, r'高盘路:\s*胜(\d+)') or '0')
    high_lose = int(re_find(text, r'高盘路:\s*胜\d+\s*平\d+\s*负(\d+)') or '0')
    high_total = high_win + int(re_find(text, r'高盘路:\s*胜\d+\s*平(\d+)') or '0') + high_lose
    if high_total > 0:
        match_score = (high_win - high_lose) / high_total
        score = score * 0.6 + match_score * 0.4

    return {
        'score': max(-1, min(1, score)),
        'win_rate': home_win_rate,
        'cover_rate': home_cover_rate,
        'total': home_total,
    }

# ============ Signal 5: 客队客场（step14-18）============
def analyze_away_team(text):
    """从客队客场分析提取信号（反向：客队利好=对主队利空）"""
    away_win_rate = re_find_float(text, r'胜率\s*([\d.]+)%')
    away_cover_rate = re_find_float(text, r'赢盘率\s*([\d.]+)%')
    away_total = int(re_find(text, r'共(\d+)\s*场') or '0')

    if away_total < 1:
        return {'score': 0, 'win_rate': 0, 'cover_rate': 0, 'total': 0}

    score = (away_win_rate - 50) / 50  # 客队胜率高→利好客→对主队是负方向

    # 盘路匹配度
    high_win = int(re_find(text, r'高盘路:\s*胜(\d+)') or '0')
    high_lose = int(re_find(text, r'高盘路:\s*胜\d+\s*平\d+\s*负(\d+)') or '0')
    high_total = high_win + int(re_find(text, r'高盘路:\s*胜\d+\s*平(\d+)') or '0') + high_lose
    if high_total > 0:
        match_score = (high_win - high_lose) / high_total
        score = score * 0.6 + match_score * 0.4

    return {
        'score': max(-1, min(1, score)),
        'win_rate': away_win_rate,
        'cover_rate': away_cover_rate,
        'total': away_total,
    }

# ============ Signal 6: 百家对比（step19-23）============
def analyze_baijia(text):
    """从百家对比提取信号"""
    # 统计所有盘路匹配度
    all_wins = 0
    all_draws = 0
    all_losses = 0
    sections = re.findall(r'(高|中|低)盘路:\s*胜(\d+)\s*平(\d+)\s*负(\d+)', text)
    for lv, s, d, l in sections:
        all_wins += int(s)
        all_draws += int(d)
        all_losses += int(l)

    total = all_wins + all_draws + all_losses
    if total < 1:
        return {'score': 0, 'total': 0}

    score = (all_wins - all_losses) / total
    return {
        'score': max(-1, min(1, score)),
        'total': total,
        'wins': all_wins,
        'draws': all_draws,
        'losses': all_losses,
    }

# ============ Signal 7: 盘路匹配汇总（step24）============
def analyze_panlu_match(text):
    """从盘路匹配JSON提取信号"""
    if not text or not text.strip():
        return {'score': 0, 'total': 0}
    try:
        data = json.loads(text)
    except:
        return {'score': 0, 'total': 0}

    # 统计各维度匹配结果
    wins = 0
    losses = 0
    total = 0
    for key, val in data.items():
        if isinstance(val, dict):
            for k2, v2 in val.items():
                if v2 == '胜': wins += 1; total += 1
                elif v2 == '负': losses += 1; total += 1
                elif v2 in ['平', '走']: total += 1
        elif val in ['胜']: wins += 1; total += 1
        elif val in ['负']: losses += 1; total += 1

    if total < 1:
        return {'score': 0, 'total': 0}

    score = (wins - losses) / total
    return {'score': max(-1, min(1, score)), 'total': total, 'wins': wins, 'losses': losses}

# ============ Signal 8: 庄家盈亏（step25）============
def analyze_zhuangjia(text):
    """从庄家盈亏分析提取信号"""
    if not text or not text.strip().startswith('{'):
        return {'score': 0, 'data': None}
    try:
        data = json.loads(text)
    except:
        return {'score': 0, 'data': None}

    labels = data.get('labels', {})
    if not labels:
        return {'score': 0, 'data': None}

    # 投注占比多 → 热度高 → 庄家可能不让他赢
    # 庄家盈亏为正 → 庄家赚钱 → 结果符合庄家预期
    # 综合判断
    home_bet = labels.get('主胜', {}).get('bet_pct', '')
    draw_bet = labels.get('平局', {}).get('bet_pct', '')
    away_bet = labels.get('客胜', {}).get('bet_pct', '')

    home_profit = labels.get('主胜', {}).get('profit', '')
    away_profit = labels.get('客胜', {}).get('profit', '')

    score = 0
    # 投注热度反着看：热度高的一方庄家可能不让赢
    if home_bet == '多' and away_bet != '多':
        score -= 0.3  # 主胜热，不利主
    elif away_bet == '多' and home_bet != '多':
        score += 0.3  # 客胜热，不利客

    # 庄家盈亏：某方庄家亏损 → 该方打出
    if home_profit in ['多'] and away_profit not in ['多']:
        score -= 0.3  # 主胜让庄家亏，主胜打出
    elif away_profit in ['多'] and home_profit not in ['多']:
        score += 0.3  # 客胜让庄家亏，客胜打出

    return {'score': max(-1, min(1, score)), 'data': labels}

# ============ Run all signals ============
europe = analyze_europe_odds(s1)
jc_same = analyze_same_odds(s2, '竞彩同赔')
iw_same = analyze_same_odds(s3, 'IW同赔')
macau = analyze_macau_asian(s6, s7, s8)
home = analyze_home_team(s9_13)
away = analyze_away_team(s14_18)
baijia = analyze_baijia(s19_23)
panlu = analyze_panlu_match(s24)
zhuangjia = analyze_zhuangjia(s25)

signals = [
    ('欧赔趋势', europe['score'], 0.12),
    ('竞彩同赔', jc_same['score'], 0.10),
    ('IW同赔', iw_same['score'], 0.08),
    ('澳门亚盘', macau['score'], 0.20),
    ('主队主场', home['score'], 0.15),
    ('客队客场', away['score'] * -1, 0.15),  # 客队利好=主队利空
    ('百家对比', baijia['score'], 0.12),
    ('盘路匹配', panlu['score'], 0.05),
    ('庄家盈亏', zhuangjia['score'], 0.03),
]

# ============ Weighted total ============
total_score = 0
total_weight = 0
evidence = []

for name, score, weight in signals:
    total_score += score * weight
    total_weight += weight
    evidence.append((name, score, weight))

final_score = total_score / total_weight if total_weight > 0 else 0
final_score = max(-1, min(1, final_score))

# ============ Generate text ============
# 方向判断
if final_score > 0.25:
    direction = f'{home_name}胜'
    direction_short = '主胜'
elif final_score < -0.25:
    direction = f'{away_name}胜'
    direction_short = '客胜'
else:
    direction = '平局'
    direction_short = '平局'

# 信心度
abs_score = abs(final_score)
if abs_score >= 0.5:
    confidence_pct = min(95, 70 + int(abs_score * 50))
    confidence_level = '强'
elif abs_score >= 0.25:
    confidence_pct = min(85, 55 + int(abs_score * 60))
    confidence_level = '中'
else:
    confidence_pct = 40 + int(abs_score * 40)
    confidence_level = '弱'

# 生成依据列表
evidence_text = []
if europe['score'] != 0:
    dir_word = '下调主胜' if europe['score'] > 0 else '下调客胜'
    evidence_text.append(f'欧赔趋势：{dir_word}（分值{europe["score"]:+.2f}）')

if jc_same['total'] >= 1:
    wr = jc_same['win_rate'] * 100
    evidence_text.append(f'竞彩同赔{jc_same["total"]}场：主胜{wr:.0f}%（分值{jc_same["score"]:+.2f}）')

if iw_same['total'] >= 1:
    evidence_text.append(f'IW同赔{iw_same["total"]}场：主胜{iw_same["win_rate"]*100:.0f}%（分值{iw_same["score"]:+.2f}）')

if macau['score'] != 0:
    macau_detail = '; '.join(f'{n}主胜{(s+1)/2*100:.0f}%' for n, s, c in macau.get('details', []) if c > 0)
    evidence_text.append(f'澳门亚盘：{macau_detail}（分值{macau["score"]:+.2f}）')

if home['total'] >= 1:
    evidence_text.append(f'{home_name}主场：胜率{home["win_rate"]:.0f}% 赢盘率{home["cover_rate"]:.0f}%（分值{home["score"]:+.2f}）')

if away['total'] >= 1:
    evidence_text.append(f'{away_name}客场：胜率{away["win_rate"]:.0f}% 赢盘率{away["cover_rate"]:.0f}%（分值{away["score"]:+.2f}）')

if baijia['total'] >= 1:
    evidence_text.append(f'百家对比{baijia["total"]}场：主胜{baijia["wins"]} 平{baijia["draws"]} 客胜{baijia["losses"]}（分值{baijia["score"]:+.2f}）')

if panlu['total'] >= 1:
    evidence_text.append(f'盘路匹配{panlu["total"]}项：胜{panlu["wins"]} 负{panlu["losses"]}（分值{panlu["score"]:+.2f}）')

# 风险识别
risks = []
if home['total'] < 3:
    risks.append(f'{home_name}主场样本不足（仅{home["total"]}场）')
if away['total'] < 3:
    risks.append(f'{away_name}客场样本不足（仅{away["total"]}场）')
if jc_same['total'] < 3:
    risks.append('竞彩同赔样本较少')
if macau.get('details'):
    for n, s, c in macau['details']:
        if c < 5:
            risks.append(f'{n}样本较少（{c}场）')

# 输出
output = []
output.append(f'## 最终预测分析')
output.append('')
output.append(f'| 维度 | 结果 |')
output.append(f'|------|------|')
output.append(f'| **推荐** | {direction} |')
output.append(f'| **信心** | {confidence_pct}%（{confidence_level}信号） |')
output.append(f'| **综合分值** | {final_score:+.3f}（+利好主 / -利好客） |')
output.append('')
output.append('### 分析依据')
output.append('')
for i, e in enumerate(evidence_text, 1):
    output.append(f'{i}. {e}')

if risks:
    output.append('')
    output.append('### 风险提示')
    output.append('')
    for r in risks:
        output.append(f'- {r}')

output.append('')
output.append('### 各维度信号明细')
output.append('')
output.append('| 维度 | 分值 | 权重 |')
output.append('|------|------|------|')
for name, score, weight in evidence:
    dir = '利好主' if score > 0.1 else ('利好客' if score < -0.1 else '中立')
    output.append(f'| {name} | {score:+.3f} {dir} | {weight*100:.0f}% |')

output.append('')
output.append('---')
output.append('')
output.append(f'*提示：以上分析基于数据驱动规则引擎，不依赖黑盒模型。每个结论均可追溯到具体数据。投资有风险，请结合实战判断。*')
output.append('')

print('\n'.join(output))
