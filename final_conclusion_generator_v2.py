# -*- coding: utf-8 -*-
"""
竞彩预测分析引擎 V2 - 多维度组合 + 历史模式匹配
新增：
1. 投注占比分析（step25）
2. 胜平负几率计算
3. 欧赔盘路组合匹配（≥2个欧赔盘路一致时加权）
4. 历史模式学习（从feedback.json学习高准确率组合）
"""
import os, sys, re, json
from datetime import datetime

MD = sys.argv[1] if len(sys.argv) > 1 else ''
if not MD or not os.path.isdir(MD):
    print('Usage: python final_conclusion_generator_v2.py <match_dir>')
    sys.exit(1)

# ============ Paths ============
G1 = os.path.join(MD, 'group01_europe')
G2 = os.path.join(MD, 'group02_handicap')
G3 = os.path.join(MD, 'group03_asian')
G4 = os.path.join(MD, 'group04_teamA')
G5 = os.path.join(MD, 'group05_teamB')
G6 = os.path.join(MD, 'group06_baijia')

FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'learnings', 'feedback.json')

def rd(path):
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def re_find(text, pattern):
    m = re.search(pattern, text or '', re.IGNORECASE)
    return m.group(1) if m else ''

# ============ Read all step data ============
s1 = rd(os.path.join(G1, 'step01_europe_basic.md'))
s2 = rd(os.path.join(G1, 'step02_jingcai_same.md'))
s3 = rd(os.path.join(G1, 'step03_interwetten_same.md'))
s6 = rd(os.path.join(G3, 'step06_asian_basic.md'))
s7 = rd(os.path.join(G3, 'step07_macau_same.md'))
s8 = rd(os.path.join(G3, 'step08_same_league.md'))
s9_13 = rd(os.path.join(G4, 'step09_13_teamA.md'))
s14_18 = rd(os.path.join(G5, 'step14_18_teamB.md'))
s19_23 = rd(os.path.join(G6, 'step19_23_baijia.md'))

# Step24
s24_path = os.path.join(MD, 'step24_panlu_match.json')
s24 = rd(s24_path)
if not s24.strip():
    s24 = rd(os.path.join(os.path.dirname(MD), 'step24_panlu_match.json'))

# Step25 - 从data目录读取
s25 = ''
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
    """从feedback.json加载高准确率组合模式"""
    patterns = {
        'high_accuracy_combos': [],  # 准确率>60%的组合
        'low_accuracy_combos': [],   # 准确率<30%的组合
        'betting_patterns': [],      # 投注占比模式
    }
    
    if not os.path.exists(FEEDBACK_FILE):
        return patterns
    
    try:
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            feedback = json.loads(f.read())
    except:
        return patterns
    
    # 统计所有combo的准确率
    combo_stats = {}
    for date, date_data in feedback.get('dates', {}).items():
        for match in date_data.get('feedback', []):
            for combo_key, combo_data in match.get('combos', {}).items():
                if combo_key not in combo_stats:
                    combo_stats[combo_key] = {'total': 0, 'correct': 0}
                combo_stats[combo_key]['total'] += combo_data.get('total', 0)
                combo_stats[combo_key]['correct'] += combo_data.get('correct', 0)
    
    # 分类
    for combo, stats in combo_stats.items():
        if stats['total'] >= 3:  # 至少3场才有统计意义
            accuracy = stats['correct'] / stats['total']
            if accuracy >= 0.60:
                patterns['high_accuracy_combos'].append({
                    'name': combo,
                    'accuracy': accuracy,
                    'total': stats['total'],
                    'correct': stats['correct']
                })
            elif accuracy <= 0.30:
                patterns['low_accuracy_combos'].append({
                    'name': combo,
                    'accuracy': accuracy,
                    'total': stats['total'],
                    'correct': stats['correct']
                })
    
    # 按准确率排序
    patterns['high_accuracy_combos'].sort(key=lambda x: x['accuracy'], reverse=True)
    patterns['low_accuracy_combos'].sort(key=lambda x: x['accuracy'])
    
    return patterns

patterns = load_high_accuracy_patterns()

# ============ Signal 1: 欧赔趋势（step1）============
def analyze_europe_odds(text):
    if not text:
        return {'score': 0, 'total': 0, 'data': {}}
    
    # 提取初盘→终盘变化
    # 格式：初盘 2.00 3.20 3.50 → 终盘 2.10 3.10 3.40
    initial = re_find(text, r'初盘.*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)')
    final = re_find(text, r'终盘.*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)')
    
    if not initial or not final:
        return {'score': 0, 'total': 0, 'data': {}}
    
    init_parts = [float(x) for x in initial.split()]
    final_parts = [float(x) for x in final.split()]
    
    # 计算变化方向
    home_change = final_parts[0] - init_parts[0]
    draw_change = final_parts[1] - init_parts[1]
    away_change = final_parts[2] - init_parts[2]
    
    # 赔率下调=利好
    score = 0
    if home_change < -0.05:
        score += 0.5
    elif home_change > 0.05:
        score -= 0.5
    
    if draw_change < -0.05:
        score += 0.3
    elif draw_change > 0.05:
        score -= 0.3
    
    if away_change < -0.05:
        score -= 0.5
    elif away_change > 0.05:
        score += 0.5
    
    return {
        'score': max(-1, min(1, score)),
        'total': 1,
        'data': {
            'home_change': home_change,
            'draw_change': draw_change,
            'away_change': away_change
        }
    }

# ============ Signal 2: 欧赔同赔（step2/3）============
def analyze_same_odds(text, name):
    if not text:
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
    # 提取同赔统计
    # 格式：主胜X场 平Y场 客胜Z场 胜率XX%
    wins = int(re_find(text, r'主胜.*?(\d+)') or '0')
    draws = int(re_find(text, r'平.*?(\d+)') or '0')
    losses = int(re_find(text, r'客胜.*?(\d+)') or '0')
    win_rate = float(re_find(text, r'胜率.*?(\d+(?:\.\d+)?)') or '0')
    
    total = wins + draws + losses
    if total == 0:
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
    # 胜率>50%利好
    score = (win_rate - 50) / 50
    
    return {
        'score': max(-1, min(1, score)),
        'total': total,
        'win_rate': win_rate,
        'data': {'wins': wins, 'draws': draws, 'losses': losses}
    }

# ============ Signal 3: 澳门亚盘（step6/7/8）============
def analyze_macau_asian(s6_text, s7_text, s8_text):
    score = 0
    total_matches = 0
    win_rate = 0
    
    # step6: 基础亚盘
    if s6_text:
        # 提取盘口方向
        if '主让' in s6_text:
            score += 0.2
        elif '客让' in s6_text:
            score -= 0.2
    
    # step7: 澳门同赔
    if s7_text:
        macau_wins = int(re_find(s7_text, r'主胜.*?(\d+)') or '0')
        macau_draws = int(re_find(s7_text, r'平.*?(\d+)') or '0')
        macau_losses = int(re_find(s7_text, r'客胜.*?(\d+)') or '0')
        macau_total = macau_wins + macau_draws + macau_losses
        if macau_total > 0:
            macau_win_rate = macau_wins / macau_total * 100
            score += (macau_win_rate - 50) / 100 * 0.5
            total_matches += macau_total
            win_rate = macau_win_rate
    
    # step8: 同联赛同亚盘
    if s8_text:
        s8_wins = int(re_find(s8_text, r'主胜.*?(\d+)') or '0')
        s8_draws = int(re_find(s8_text, r'平.*?(\d+)') or '0')
        s8_losses = int(re_find(s8_text, r'客胜.*?(\d+)') or '0')
        s8_total = s8_wins + s8_draws + s8_losses
        if s8_total > 0:
            s8_win_rate = s8_wins / s8_total * 100
            score += (s8_win_rate - 50) / 100 * 0.3
            total_matches += s8_total
    
    return {
        'score': max(-1, min(1, score)),
        'total': total_matches,
        'win_rate': win_rate,
        'data': {'matches': total_matches}
    }

# ============ Signal 4: 主队主场（step9-13）============
def analyze_home_team(text):
    if not text:
        return {'score': 0, 'total': 0, 'win_rate': 0}
    
    # 提取主场胜率
    home_win_rate = float(re_find(text, r'胜率.*?(\d+(?:\.\d+)?)') or '0')
    home_total = int(re_find(text, r'共.*?(\d+)') or '0')
    
    if home_total == 0:
        return {'score': 0, 'total': 0, 'win_rate': 0}
    
    # 胜率>50%利好
    score = (home_win_rate - 50) / 100
    
    return {
        'score': max(-1, min(1, score)),
        'total': home_total,
        'win_rate': home_win_rate
    }

# ============ Signal 5: 客队客场（step14-18）============
def analyze_away_team(text):
    if not text:
        return {'score': 0, 'total': 0, 'win_rate': 0}
    
    away_win_rate = float(re_find(text, r'胜率.*?(\d+(?:\.\d+)?)') or '0')
    away_total = int(re_find(text, r'共.*?(\d+)') or '0')
    
    if away_total == 0:
        return {'score': 0, 'total': 0, 'win_rate': 0}
    
    # 客队胜率高=主队利空
    score = -(away_win_rate - 50) / 100
    
    return {
        'score': max(-1, min(1, score)),
        'total': away_total,
        'win_rate': away_win_rate
    }

# ============ Signal 6: 百家对比（step19-23）============
def analyze_baijia(text):
    if not text:
        return {'score': 0, 'total': 0}
    
    # 提取百家欧赔统计
    bj_wins = int(re_find(text, r'主胜.*?(\d+)') or '0')
    bj_draws = int(re_find(text, r'平.*?(\d+)') or '0')
    bj_losses = int(re_find(text, r'客胜.*?(\d+)') or '0')
    bj_total = bj_wins + bj_draws + bj_losses
    
    if bj_total == 0:
        return {'score': 0, 'total': 0}
    
    # 主胜比例>50%利好
    score = (bj_wins / bj_total - 0.5) * 2
    
    return {
        'score': max(-1, min(1, score)),
        'total': bj_total
    }

# ============ Signal 7: 盘路匹配汇总（step24）============
def analyze_panlu_match(text):
    if not text:
        return {'score': 0, 'matched_dims': 0}
    
    try:
        data = json.loads(text)
    except:
        return {'score': 0, 'matched_dims': 0}
    
    # 统计匹配维度数
    matched = 0
    for key, val in data.items():
        if 'match' in key.lower() and val:
            matched += 1
    
    # 匹配维度≥3利好
    score = min(1, matched / 5)
    
    return {
        'score': score,
        'matched_dims': matched,
        'data': data
    }

# ============ Signal 8: 庄家盈亏（step25）============
def analyze_zhuangjia(text):
    if not text:
        return {'score': 0, 'data': None, 'bet_diff': 0}
    
    try:
        data = json.loads(text)
    except:
        return {'score': 0, 'data': None, 'bet_diff': 0}
    
    labels = data.get('labels', {})
    data_section = data.get('data', {})
    
    if not labels:
        return {'score': 0, 'data': None, 'bet_diff': 0}
    
    # 提取投注占比
    home_bet = data_section.get('主胜', {}).get('bet_pct', '0')
    draw_bet = data_section.get('平局', {}).get('bet_pct', '0')
    away_bet = data_section.get('客胜', {}).get('bet_pct', '0')
    
    try:
        home_bet_pct = float(home_bet)
        draw_bet_pct = float(draw_bet)
        away_bet_pct = float(away_bet)
    except:
        home_bet_pct = draw_bet_pct = away_bet_pct = 33.3
    
    # 投注占比差值（最高-最低）
    bet_diff = max(home_bet_pct, draw_bet_pct, away_bet_pct) - min(home_bet_pct, draw_bet_pct, away_bet_pct)
    
    # 庄家盈亏
    home_profit = data_section.get('主胜', {}).get('profit', '0')
    draw_profit = data_section.get('平局', {}).get('profit', '0')
    away_profit = data_section.get('客胜', {}).get('profit', '0')
    
    try:
        home_profit_val = float(home_profit.replace(',', ''))
        draw_profit_val = float(draw_profit.replace(',', ''))
        away_profit_val = float(away_profit.replace(',', ''))
    except:
        home_profit_val = draw_profit_val = away_profit_val = 0
    
    # 逻辑：
    # 1. 投注占比高但庄家盈利高 → 庄家看好该结果
    # 2. 投注占比高但庄家亏损 → 该结果可能打不出（诱盘）
    score = 0
    
    # 投注占比差值>15%说明有明显热度
    if bet_diff > 15:
        # 找出最热选项
        max_bet = max(home_bet_pct, draw_bet_pct, away_bet_pct)
        
        if max_bet == home_bet_pct:
            # 主胜最热
            if home_profit_val > away_profit_val:
                score += 0.4  # 庄家在主胜上盈利更多，利好主
            else:
                score -= 0.3  # 庄家在主胜上亏损，可能诱盘
        elif max_bet == away_bet_pct:
            # 客胜最热
            if away_profit_val > home_profit_val:
                score -= 0.4  # 庄家在客胜上盈利更多，利好客
            else:
                score += 0.3  # 庄家在客胜上亏损，可能诱盘
        else:
            # 平局最热
            if draw_profit_val > max(home_profit_val, away_profit_val):
                score += 0.2  # 平局利好
    
    # 投注占比均匀（差值<5%）→ 难判断
    if bet_diff < 5:
        score = 0
    
    return {
        'score': max(-1, min(1, score)),
        'data': labels,
        'bet_diff': bet_diff,
        'bet_pcts': {'home': home_bet_pct, 'draw': draw_bet_pct, 'away': away_bet_pct},
        'profits': {'home': home_profit_val, 'draw': draw_profit_val, 'away': away_profit_val}
    }

# ============ Signal 9: 欧赔盘路组合匹配（新增）============
def analyze_europe_combo(s1_text, s2_text, s3_text):
    """
    分析≥2个欧赔盘路是否一致
    - step1: 欧赔趋势（初→终变化方向）
    - step2: 竞彩同赔
    - step3: IW同赔
    
    当≥2个盘路指向同一方向时，给予额外加权
    """
    e1 = analyze_europe_odds(s1_text)
    e2 = analyze_same_odds(s2_text, '竞彩')
    e3 = analyze_same_odds(s3_text, 'IW')
    
    # 判断各盘路方向
    directions = []
    if e1['score'] > 0.2:
        directions.append('home')
    elif e1['score'] < -0.2:
        directions.append('away')
    
    if e2['score'] > 0.2:
        directions.append('home')
    elif e2['score'] < -0.2:
        directions.append('away')
    
    if e3['score'] > 0.2:
        directions.append('home')
    elif e3['score'] < -0.2:
        directions.append('away')
    
    # 统计一致性
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
    
    return {
        'score': combo_score,
        'level': combo_level,
        'home_count': home_count,
        'away_count': away_count,
        'data': {'e1': e1, 'e2': e2, 'e3': e3}
    }

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
europe_combo = analyze_europe_combo(s1, s2, s3)

# ============ Calculate data quality score ============
# 数据质量分：样本越多、维度越全，分数越高
total_samples = (
    europe['total'] + jc_same['total'] + iw_same['total'] +
    macau['total'] + home['total'] + away['total'] + baijia['total']
)
active_dims = sum(1 for x in [europe, jc_same, iw_same, macau, home, away, baijia, panlu, zhuangjia] if x.get('total', 0) > 0 or x.get('matched_dims', 0) > 0)

data_quality = min(1.0, (total_samples / 50) * 0.5 + (active_dims / 9) * 0.5)

# ============ Weighted total with dynamic adjustment ============
# 基础权重
base_weights = [
    ('欧赔趋势', europe['score'], 0.10),
    ('竞彩同赔', jc_same['score'], 0.08),
    ('IW同赔', iw_same['score'], 0.06),
    ('澳门亚盘', macau['score'], 0.15),
    ('主队主场', home['score'], 0.12),
    ('客队客场', away['score'] * -1, 0.12),
    ('百家对比', baijia['score'], 0.10),
    ('盘路匹配', panlu['score'], 0.05),
    ('庄家盈亏', zhuangjia['score'], 0.07),
    ('欧赔组合', europe_combo['score'], 0.15),  # 新增：欧赔盘路组合
]

# 根据历史高准确率组合调整权重
for combo in patterns.get('high_accuracy_combos', [])[:3]:  # 取前3个高准确率组合
    if '竞彩' in combo['name'] or '同赔' in combo['name']:
        # 找到对应维度，增加权重
        for i, (name, score, weight) in enumerate(base_weights):
            if '竞彩' in name or '同赔' in name:
                base_weights[i] = (name, score, min(0.20, weight * 1.3))

# 根据数据质量调整信心度
quality_factor = 0.5 + data_quality * 0.5  # 0.5~1.0

# 计算加权总分
total_score = sum(score * weight for name, score, weight in base_weights)
total_weight = sum(weight for name, score, weight in base_weights)
final_score = total_score / total_weight if total_weight > 0 else 0
final_score = final_score * quality_factor  # 数据质量调整
final_score = max(-1, min(1, final_score))

# ============ Calculate confidence based on multiple factors ============
abs_score = abs(final_score)

# 信心度 = 分值大小 + 数据质量 + 维度一致性
confidence_base = 40 + int(abs_score * 40)  # 基础信心40-80%
confidence_quality = int(data_quality * 20)  # 数据质量加成0-20%
confidence_consistency = 0

# 维度一致性加分
if europe_combo['home_count'] >= 2 or europe_combo['away_count'] >= 2:
    confidence_consistency += 10

confidence_pct = min(95, confidence_base + confidence_quality + confidence_consistency)

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
# 方向判断
if final_score > 0.15:
    direction = '主胜'
    direction_short = '主胜'
elif final_score < -0.15:
    direction = '客胜'
    direction_short = '客胜'
else:
    direction = '平局'
    direction_short = '平局'

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
if europe_combo['level'] != '无一致' and abs_score < 0.3:
    risks.append('欧赔盘路分歧')

# 高准确率组合提示
high_combo_tips = []
for combo in patterns.get('high_accuracy_combos', [])[:2]:
    high_combo_tips.append(f"{combo['name']}（历史{combo['accuracy']*100:.0f}%）")

# ============ Output ============
output = []
output.append('## 最终预测分析（V2 - 多维度组合）')
output.append('')
output.append('| 维度 | 结果 |')
output.append('|------|------|')
output.append(f'| **推荐** | {direction} |')
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
output.append(f'- {europe_combo["level"]}')
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
    if abs(score) > 0.05 or weight >= 0.10:
        trend = '利好主' if score > 0 else ('利好客' if score < 0 else '中立')
        output.append(f'| {name} | {score:+.3f} {trend} | {weight*100:.0f}% |')
output.append('')
output.append('---')
output.append('')
output.append('*提示：以上分析基于数据驱动规则引擎 + 历史模式学习，每个结论均可追溯到具体数据。投资有风险，请结合实战判断。*')

print('\n'.join(output))
