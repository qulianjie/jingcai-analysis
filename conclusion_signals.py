# -*- coding: utf-8 -*-
"""
信号提取函数模块 - 从 final_conclusion_generator.py 拆分
包含所有 analyze_* 分析函数和计算工具函数
"""
import re, os, json, math
from _util import rd, re_find, ensure_utf8_stdout
from _log_util import setup_logger
def analyze_europe_odds(text):
    if not text:
        return {'score': 0, 'total': 0, 'data': {}}
    
    # 从表格中提取竞彩官方数据
    # 格式: | 竞彩官方 | 1.13 | 8.50 | 15.00 | 1.08 | 10.00 | 23.00 | ⬇⬆⬆ |
    import re as re2
    row_match = re2.search(r'竞彩官方\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)\s*\|\s*(\d+\.\d+)', text)
    
    if not row_match:
        # fallback: 初盘/终盘格式
        initial = re_find(text, r'初盘.*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)')
        final = re_find(text, r'终盘.*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)')
        if not initial or not final:
            return {'score': 0, 'total': 0, 'data': {}}
        init_parts = [float(x) for x in initial.split()]
        final_parts = [float(x) for x in final.split()]
    else:
        init_parts = [float(row_match.group(i)) for i in [1, 2, 3]]
        final_parts = [float(row_match.group(i)) for i in [4, 5, 6]]
    
    home_change = final_parts[0] - init_parts[0]
    draw_change = final_parts[1] - init_parts[1]
    away_change = final_parts[2] - init_parts[2]
    
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

# ============ Signal 2: 欧赔同赔（step2/3/5）============

def analyze_same_odds(text, name):
    if not text or '无同赔数据' in text:
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
    # 提取当前联赛名（从step1或step6）
    current_league = ''
    league_match = re.search(r'当前联赛：\s*(.+)', text)
    if league_match:
        current_league = league_match.group(1).strip()
    
    # 从表格行中提取每场比赛，按盘路匹配度分层加权
    # 表格格式: | 赛事 | 日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路变化 | 盘路匹配度 | 联赛 |
    rows = []
    for line in text.split('\n'):
        if '|' not in line or '---' in line or '赛事' in line:
            continue
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if len(cells) < 8:
            continue
        
        # 赛果在第4列(索引3)
        result = cells[3] if len(cells) > 3 else ''
        if result not in ['胜', '平', '负']:
            continue
        
        # 盘路匹配度在第8列(索引7)
        panlu = cells[7] if len(cells) > 7 else '低'
        
        # 联赛在第9列(索引8)
        league = cells[8] if len(cells) > 8 else ''
        
        rows.append({
            'result': result,
            'panlu': panlu,
            'league': league.strip(),
            'is_same_league': current_league and league.strip() == current_league
        })
    
    if not rows:
        # fallback: 从统计行提取
        stats_match = re.search(r'胜(\d+)\s+平(\d+)\s+负(\d+)', text)
        if stats_match:
            wins = int(stats_match.group(1))
            draws = int(stats_match.group(2))
            losses = int(stats_match.group(3))
            total = wins + draws + losses
            win_rate = wins / total * 100 if total > 0 else 0
            score = (win_rate - 50) / 50
            return {
                'score': max(-1, min(1, score)),
                'total': total,
                'win_rate': win_rate,
                'data': {'wins': wins, 'draws': draws, 'losses': losses}
            }
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
    # 分层加权计分
    # 权重: 高+同联赛=3, 高=2, 中+同联赛=1.5, 中=1, 低=0.5
    tier_weights = {
        ('高', True): 3.0,    # 盘路匹配度高 + 同联赛
        ('高', False): 2.0,   # 盘路匹配度高
        ('中', True): 1.5,    # 盘路匹配度中 + 同联赛
        ('中', False): 1.0,   # 盘路匹配度中
        ('低', True): 0.75,   # 盘路匹配度低 + 同联赛
        ('低', False): 0.5,   # 盘路匹配度低
    }
    
    weighted_home = 0  # 胜
    weighted_draw = 0
    weighted_away = 0  # 负
    total_weight = 0
    
    for row in rows:
        weight = tier_weights.get((row['panlu'], row['is_same_league']), 0.5)
        total_weight += weight
        
        if row['result'] == '胜':
            weighted_home += weight
        elif row['result'] == '平':
            weighted_draw += weight
        elif row['result'] == '负':
            weighted_away += weight
    
    if total_weight == 0:
        return {'score': 0, 'total': len(rows), 'win_rate': 0, 'data': {}}
    
    # 计算加权胜率
    weighted_win_rate = weighted_home / total_weight * 100
    
    # 分值: +1=全主胜, -1=全客胜, 0=均衡
    score = (weighted_win_rate - 50) / 50
    
    return {
        'score': max(-1, min(1, score)),
        'total': len(rows),
        'win_rate': weighted_win_rate,
        'data': {
            'weighted_home': weighted_home,
            'weighted_draw': weighted_draw,
            'weighted_away': weighted_away,
            'total_weight': total_weight,
            'tier_breakdown': {
                '高+同联赛': sum(1 for r in rows if r['panlu']=='高' and r['is_same_league']),
                '高': sum(1 for r in rows if r['panlu']=='高' and not r['is_same_league']),
                '中+同联赛': sum(1 for r in rows if r['panlu']=='中' and r['is_same_league']),
                '中': sum(1 for r in rows if r['panlu']=='中' and not r['is_same_league']),
                '低': sum(1 for r in rows if r['panlu']=='低'),
            }
        }
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
        # 尝试多种格式: "胜4 平0 负0" 或 "主胜.*?4" 或 "胜.*?4"
        macau_match = re.search(r'胜(\d+)\s+平(\d+)\s+负(\d+)', s7_text)
        if macau_match:
            macau_wins = int(macau_match.group(1))
            macau_draws = int(macau_match.group(2))
            macau_losses = int(macau_match.group(3))
        else:
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
        s8_match = re.search(r'胜(\d+)\s+平(\d+)\s+负(\d+)', s8_text)
        if s8_match:
            s8_wins = int(s8_match.group(1))
            s8_draws = int(s8_match.group(2))
            s8_losses = int(s8_match.group(3))
        else:
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
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
    # 提取主场胜率
    home_win_rate = float(re_find(text, r'胜率.*?(\d+(?:\.\d+)?)') or '0')
    home_total = int(re_find(text, r'共.*?(\d+)') or '0')
    
    if home_total == 0:
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
    # 胜率>50%利好
    score = (home_win_rate - 50) / 100
    
    return {
        'score': max(-1, min(1, score)),
        'total': home_total,
        'win_rate': home_win_rate,
        'data': {'home_win_rate': home_win_rate}
    }

# ============ Signal 5: 客队客场（step14-18）============

def analyze_away_team(text):
    if not text:
        return {'score': 0, 'total': 0, 'win_rate': 0, 'data': {}}
    
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
        return {'score': 0, 'total': 0, 'data': {}}
    
    # 提取百家欧赔统计
    bj_wins = int(re_find(text, r'主胜.*?(\d+)') or '0')
    bj_draws = int(re_find(text, r'平.*?(\d+)') or '0')
    bj_losses = int(re_find(text, r'客胜.*?(\d+)') or '0')
    bj_total = bj_wins + bj_draws + bj_losses
    
    if bj_total == 0:
        return {'score': 0, 'total': 0, 'data': {}}
    
    # 主胜比例>50%利好
    score = (bj_wins / bj_total - 0.5) * 2
    
    return {
        'score': max(-1, min(1, score)),
        'total': bj_total
    }

# ============ Signal 7: 盘路匹配汇总（step24）============

def analyze_panlu_match(text):
    if not text:
        return {'score': 0, 'matched_dims': 0, 'data': {}}
    
    # step24文件虽然扩展名为.json，但实际内容是Markdown文本
    # 需要同时支持JSON和Markdown两种格式
    # 尝试从文本中提取胜平负统计
    wins = len(re.findall(r'[|\s]胜[|\s]', text))
    draws = len(re.findall(r'[|\s]平[|\s]', text))
    losses = len(re.findall(r'[|\s]负[|\s]', text))
    
    total = wins + draws + losses
    if total > 0:
        score = (wins - losses) / total
        return {
            'score': max(-1, min(1, score)),
            'matched_dims': total,
            'wins': wins, 'draws': draws, 'losses': losses,
            'data': {'wins': wins, 'draws': draws, 'losses': losses}
        }
    
    # 回退：尝试JSON格式（旧版本兼容）
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
# 替代旧的简单线性调整，解决三个问题：
# 1. 不看样本量 → Wilson Score 置信区间
# 2. 只增不减 → 低准确率组合惩罚
# 3. 线性boost粗糙 → 非线性映射 + 分层修正


def _wilson(correct, total, z=1.96):
    """Wilson Score 置信下界"""
    if total == 0:
        return 0.0
    p = correct / total
    z2 = z * z
    center = p + z2 / (2 * total)
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total)
    return (center - margin) / (1 + z2 / total)


def _bayesian(correct, total, C=10, m=0.50):
    """Bayesian Average 平滑评分"""
    if total == 0:
        return m
    return (C * m + total * correct / total) / (C + total)


def _trust_to_factor(trust):
    """综合可信分 → 权重修正系数 (平滑非线性)
    
    修复：缩小boost/penalty范围，避免极端权重变化
    旧版: trust≥0.60→×1.0~1.5, trust<0.20→×0.3~0.8 (太激进)
    新版: trust≥0.60→×1.0~1.25, trust<0.20→×0.6~0.9 (温和)
    """
    if trust >= 0.60:
        return 1.0 + min(0.25, (trust - 0.60) / 0.40 * 0.25)
    elif trust >= 0.40:
        return 1.0
    elif trust >= 0.20:
        return 0.85 + (trust - 0.20) / 0.20 * 0.15
    elif trust > 0.0:
        return 0.6 + (trust / 0.20) * 0.25
    return 0.0


