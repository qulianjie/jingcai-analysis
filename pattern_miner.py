# -*- coding: utf-8 -*-
"""
智能规律发现引擎 - Pattern Discovery Engine
==========================================
从历史竞彩数据中自动发现规律、验证假设、生成规则

发现的规则类型:
  1. 同赔集中度 → 预测准确率
  2. 联赛特性 → 胜平负分布异常
  3. 盘线类型 → 赛果倾向
  4. 多信号组合 → 准确率提升
  5. 信心度校准 → 信心 vs 实际准确率
  6. 盘路匹配 → 历史盘路重复率
"""
import os, sys, json, re
from collections import defaultdict, Counter
from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def safe_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def safe_md(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

def get_results(date_str):
    """获取赛果"""
    rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str))
    if os.path.exists(rf):
        d = safe_json(rf)
        if d:
            return d.get(date_str, d)
    return {}

def extract_prediction_from_md(content):
    """从同赔markdown提取胜/平/负计数"""
    win = draw = loss = 0
    
    # Match patterns like: 胜(3) 平(2) 负(1) or 主胜(5) 平(3) 客负(2)
    for m in re.findall(r'(?:主)?胜\s*\((\d+)\)', content):
        win += int(m)
    for m in re.findall(r'平\s*\((\d+)\)', content):
        draw += int(m)
    for m in re.findall(r'(?:客)?负\s*\((\d+)\)', content):
        loss += int(m)
    
    if win + draw + loss == 0:
        return None
    
    return {'win': win, 'draw': draw, 'loss': loss, 'total': win + draw + loss}

def get_match_dir(date_str):
    """获取某天的match数据目录"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return None
    
    data_dir = os.path.join(task_dir, 'data')
    if os.path.exists(data_dir):
        return data_dir
    return task_dir

def collect_match_data(date_str):
    """收集某天的所有比赛数据"""
    data_dir = get_match_dir(date_str)
    if not data_dir:
        return []
    
    matches = []
    results = get_results(date_str)
    
    for mdir in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, mdir)
        if not os.path.isdir(mp):
            continue
        
        meta = safe_json(os.path.join(mp, 'meta.json'))
        if not meta:
            continue
        
        match = {
            'date': date_str,
            'matchnum': meta.get('matchnum', ''),
            'home': meta.get('home', ''),
            'away': meta.get('away', ''),
            'league': meta.get('league', ''),
            'macau_line': meta.get('macau_line', ''),
        }
        
        # 赛果
        mn_match = re.search(r'(\d{3})', meta.get('matchnum', ''))
        if mn_match:
            mn = mn_match.group(1)
            r = results.get(mn, {})
            match['actual'] = r.get('result', '')
            match['score'] = r.get('score', '')
        else:
            match['actual'] = ''
            match['score'] = ''
        
        # 竞彩同赔
        s2 = safe_md(os.path.join(mp, 'group01_europe', 'step02_jingcai_same.md'))
        match['s2'] = extract_prediction_from_md(s2)
        
        # 让球同赔
        s5 = safe_md(os.path.join(mp, 'group02_handicap', 'step05_handicap_same.md'))
        match['s5'] = extract_prediction_from_md(s5)
        
        # 澳门同赔
        s7 = safe_md(os.path.join(mp, 'group03_asian', 'step07_macau_same.md'))
        match['s7'] = extract_prediction_from_md(s7)
        
        matches.append(match)
    
    return matches

# ============ 规律发现引擎 ============

def mine_concentration_accuracy(matches):
    """规则1: 同赔集中度 vs 准确率"""
    log('RULE', '=== 规则1: 同赔集中度 vs 准确率 ===')
    
    buckets = {
        'high(>60%)': {'ok':0,'total':0},
        'mid(40-60%)': {'ok':0,'total':0},
        'low(<40%)': {'ok':0,'total':0},
    }
    
    for m in matches:
        if not m.get('actual') or m['actual'] == '待查':
            continue
        
        for step in ['s2', 's5', 's7']:
            pred = m.get(step)
            if not pred or pred['total'] == 0:
                continue
            
            max_c = max(pred['win'], pred['draw'], pred['loss'])
            conc = max_c / pred['total']
            
            if max_c == pred['win']: predicted = '胜'
            elif max_c == pred['draw']: predicted = '平'
            else: predicted = '负'
            
            correct = (predicted == m['actual'])
            
            if conc > 0.6: b = buckets['high(>60%)']
            elif conc > 0.4: b = buckets['mid(40-60%)']
            else: b = buckets['low(<40%)']
            
            b['total'] += 1
            if correct: b['ok'] += 1
    
    for name, b in buckets.items():
        if b['total'] > 0:
            rate = b['ok'] / b['total'] * 100
            log('DATA', '集中度{}: {}/{} = {:.1f}%'.format(name, b['ok'], b['total'], rate))
            if b['total'] >= 3 and rate > 65:
                log('RULE', '✅ 集中度>60%时准确率{:.1f}%（样本{}）'.format(rate, b['total']))
            elif b['total'] >= 5 and rate < 45:
                log('RULE', '⚠️ 集中度<40%时准确率仅{:.1f}%（样本{}）'.format(rate, b['total']))

def mine_league_distribution(matches):
    """规则2: 联赛赛果分布异常"""
    log('RULE', '=== 规则2: 联赛赛果分布 ===')
    
    league = defaultdict(lambda: {'total':0, '胜':0, '平':0, '负':0})
    
    for m in matches:
        if not m.get('actual') or m['actual'] == '待查':
            continue
        lg = m.get('league', '未知')
        league[lg]['total'] += 1
        league[lg][m['actual']] += 1
    
    for lg, d in sorted(league.items(), key=lambda x: x[1]['total'], reverse=True):
        if d['total'] < 2:
            continue
        t = d['total']
        w_rate = d['胜']/t*100
        draw_rate = d['平']/t*100
        l_rate = d['负']/t*100
        log('DATA', '{}: 总{} 胜{:.0f}% 平{:.0f}% 负{:.0f}%'.format(lg, t, w_rate, draw_rate, l_rate))
        
        if draw_rate > 50:
            log('RULE', '🔥 {}平局率极高({:.0f}%, {}场) → 优先选平局'.format(lg, draw_rate, t))
        if w_rate < 20:
            log('RULE', '🔥 {}主胜极少({:.0f}%, {}场) → 避免选主胜'.format(lg, w_rate, t))

def mine_macau_line(matches):
    """规则3: 澳门盘线 vs 赛果"""
    log('RULE', '=== 规则3: 澳门盘线 vs 赛果 ===')
    
    stats = defaultdict(lambda: {'total':0, '胜':0, '平':0, '负':0})
    
    for m in matches:
        if not m.get('actual') or m['actual'] == '待查':
            continue
        line = m.get('macau_line', '')
        if not line:
            continue
        stats[line]['total'] += 1
        stats[line][m['actual']] += 1
    
    for line, d in sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True):
        if d['total'] < 2:
            continue
        t = d['total']
        log('DATA', '{}: 总{} 胜{:.0f}% 平{:.0f}% 负{:.0f}%'.format(
            line[:12], t, d['胜']/t*100, d['平']/t*100, d['负']/t*100))

def mine_multi_signal(matches):
    """规则4: 多信号一致性 vs 准确率"""
    log('RULE', '=== 规则4: 多信号一致性 vs 准确率 ===')
    
    stats = {
        '全部一致': {'ok':0,'total':0},
        '多数一致': {'ok':0,'total':0},
        '信号分歧': {'ok':0,'total':0},
    }
    
    for m in matches:
        if not m.get('actual') or m['actual'] == '待查':
            continue
        
        preds = []
        for key in ['s2', 's5', 's7']:
            p = m.get(key)
            if p and p['total'] > 0:
                max_c = max(p['win'], p['draw'], p['loss'])
                if max_c == p['win']: preds.append('胜')
                elif max_c == p['draw']: preds.append('平')
                else: preds.append('负')
        
        if len(preds) < 2:
            continue
        
        counts = Counter(preds)
        top_pred, top_count = counts.most_common(1)[0]
        correct = (top_pred == m['actual'])
        
        if top_count == len(preds):
            b = stats['全部一致']
        elif top_count >= len(preds) * 0.6:
            b = stats['多数一致']
        else:
            b = stats['信号分歧']
        
        b['total'] += 1
        if correct: b['ok'] += 1
    
    for name, b in stats.items():
        if b['total'] > 0:
            rate = b['ok'] / b['total'] * 100
            log('DATA', '{}: {}/{} = {:.1f}%'.format(name, b['ok'], b['total'], rate))
            if name == '全部一致' and b['total'] >= 2 and rate > 65:
                log('RULE', '🔥 多信号一致时准确率{:.1f}%（样本{}）'.format(rate, b['total']))

def mine_confidence_calibration(matches):
    """规则5: 信心度校准"""
    log('RULE', '=== 规则5: 信心度校准 ===')
    
    stats = {
        '强(>60%)': {'ok':0,'total':0},
        '中(40-60%)': {'ok':0,'total':0},
        '弱(<40%)': {'ok':0,'total':0},
    }
    
    task_dir = os.path.join(TASKS_DIR, matches[0]['date']) if matches else None
    if not task_dir or not os.path.exists(task_dir):
        log('SKIP', '无报告文件')
        return
    
    results = get_results(matches[0]['date'])
    
    for f in os.listdir(task_dir):
        if not f.endswith('.md'):
            continue
        
        content = safe_md(os.path.join(task_dir, f))
        if not content:
            continue
        
        conf_match = re.search(r'\*\*信心\*\*\s*\|\s*([^\|]+)', content)
        if not conf_match:
            continue
        
        conf_text = conf_match.group(1).strip()
        pct_match = re.search(r'(\d+)%', conf_text)
        if not pct_match:
            continue
        pct = int(pct_match.group(1))
        
        rec_match = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
        if not rec_match:
            continue
        rec = rec_match.group(1).strip()
        
        pred = ''
        if '主胜' in rec or ('胜' in rec and '客' not in rec):
            pred = '胜'
        elif '客胜' in rec:
            pred = '负'
        elif '平局' in rec or ('平' in rec and '胜' not in rec and '负' not in rec):
            pred = '平'
        
        if not pred:
            continue
        
        mn_match = re.search(r'(\d{3})', f)
        if not mn_match:
            continue
        mn = mn_match.group(1)
        actual = results.get(mn, {}).get('result', '')
        
        if not actual or actual == '待查':
            continue
        
        correct = (pred == actual)
        
        if pct > 60: b = stats['强(>60%)']
        elif pct > 40: b = stats['中(40-60%)']
        else: b = stats['弱(<40%)']
        
        b['total'] += 1
        if correct: b['ok'] += 1
    
    for name, b in stats.items():
        if b['total'] > 0:
            rate = b['ok'] / b['total'] * 100
            log('DATA', '{}: {}/{} = {:.1f}%'.format(name, b['ok'], b['total'], rate))
            if b['total'] >= 3:
                if rate > 60:
                    log('RULE', '✅ {name}准确率达{rate:.1f}%'.format(name=name, rate=rate))
                else:
                    log('RULE', '⚠️ {name}仅{rate:.1f}% — 信心度可能高估'.format(name=name, rate=rate))

def main():
    log('START', '=== Pattern Discovery Engine ===')
    
    # 收集所有有赛果的日期
    dates_with_results = []
    if os.path.exists(TASKS_DIR):
        for d in sorted(os.listdir(TASKS_DIR)):
            if re.match(r'\d{4}-\d{2}-\d{2}', d):
                results = get_results(d)
                if results:
                    dates_with_results.append(d)
    
    log('INFO', '有赛果的日期: {}'.format(', '.join(dates_with_results) if dates_with_results else '无'))
    
    all_rules = {}
    
    for date_str in dates_with_results:
        log('DATE', '====== {} ======'.format(date_str))
        
        matches = collect_match_data(date_str)
        with_result = sum(1 for m in matches if m.get('actual') and m['actual'] != '待查')
        log('INFO', '比赛: {}场, 有赛果: {}场'.format(len(matches), with_result))
        
        if not matches:
            continue
        
        mine_concentration_accuracy(matches)
        print('')
        mine_league_distribution(matches)
        print('')
        mine_macau_line(matches)
        print('')
        mine_multi_signal(matches)
        print('')
        mine_confidence_calibration(matches)
        
        print('')
    
    log('DONE', 'Pattern Discovery 完成')

if __name__ == '__main__':
    main()
