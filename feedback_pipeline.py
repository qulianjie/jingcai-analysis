#!/usr/bin/env python3
"""
竞彩反馈流水线 - Python实现
替换 feedback.js (因 Windows Node.js 网络不通，Windows Python 网络可用)
"""

import requests
import json
import re
import os
import sys
import time
from datetime import datetime, timedelta

WORKSPACE = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
DATA_DIR = os.path.join(WORKSPACE, '..', 'data', 'jingcai')
NOTION_KEY = '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'
NOTION_DB = '35491ad7-17ba-81cc-aa04-ce53f7234e17'
NOTION_VER = '2022-06-28'
NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_KEY}',
    'Notion-Version': NOTION_VER,
    'Content-Type': 'application/json'
}

# ===== Helper: 预测转结果 =====
def pred_to_result(pred):
    if not pred: return None
    if '让球胜' in pred or '让球主胜' in pred: return '胜'
    if '让球负' in pred or '让球客胜' in pred: return '负'
    if '让球平' in pred: return '平'
    if '主胜' in pred: return '胜'
    if '客胜' in pred: return '负'
    if '平局' in pred or pred == '平': return '平'
    if '3' in pred: return '胜'
    if '0' in pred: return '负'
    if '1' in pred: return '平'
    return None

# ===== Step 1: 查询 Notion 比赛 =====
def query_notion_matches(date_str):
    url = f'https://api.notion.com/v1/databases/{NOTION_DB}/query'
    body = {
        "filter": {
            "and": [{"property": "比赛日期", "date": {"equals": date_str}}]
        },
        "page_size": 100
    }
    r = requests.post(url, headers=NOTION_HEADERS, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    pages = data.get('results', [])
    print(f'  找到 {len(pages)} 场比赛')
    return pages

# ===== Step 2: 获取比赛结果 =====
def fetch_match_results(date_str):
    """从500.com获取赛果，使用 curl (WSL) 或 Python requests"""
    results = {}
    url = f'https://trade.500.com/jczq/?playid=269&g=2&date={date_str}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = 'gbk'
        html = r.text
    except Exception as e:
        print(f'  ⚠️ requests 失败: {e}，改用 curl')
        # Fallback: use curl from WSL
        import subprocess
        result = subprocess.run(
            ['curl', '-s', '--connect-timeout', '15', url, '-H', f'User-Agent: {headers["User-Agent"]}'],
            capture_output=True, text=True, timeout=30
        )
        html = result.stdout
        # Decode GBK
        try:
            html = html.encode('latin1').decode('gbk')
        except:
            pass
    
    # Parse matches - same regex as feedback.js
    tr_pattern = re.compile(r'<tr[^>]*class="[^"]*bet-tb-tr[^"]*"[^>]*>([\s\S]*?)</tr>')
    for tr_match in tr_pattern.finditer(html):
        full = tr_match.group(0)
        mn_m = re.search(r'data-matchnum="([^"]+)"', full)
        if not mn_m: continue
        match_num = mn_m.group(1).strip()
        
        team_td = re.search(r'<td[^>]*class="[^"]*td-team[^"]*"[^>]*>([\s\S]*?)</td>', tr_match.group(1))
        if not team_td: continue
        team_text = re.sub(r'<[^>]*>', '', team_td.group(1)).strip()
        
        if 'VS' not in team_text:
            score_m = re.search(r'(\d+):(\d+)', team_text)
            if score_m:
                hs, aw = int(score_m.group(1)), int(score_m.group(2))
                if hs <= 20 and aw <= 20:
                    results[match_num] = {'homeScore': hs, 'awayScore': aw}
    
    print(f'  获取到 {len(results)} 场赛果')
    return results

# ===== Step 3: 读取本地终盘赔率 =====
def fetch_final_odds(date_str):
    """从 task/<date>/data/match*/ 目录提取赔率数据"""
    odds = {}
    task_dir = os.path.join(WORKSPACE, 'tasks', date_str)
    data_dir = os.path.join(task_dir, 'data')
    
    if not os.path.exists(data_dir):
        print(f'  ⚠️ 数据目录不存在: {data_dir}')
        return odds
    
    match_dirs = [d for d in os.listdir(data_dir)
                  if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))]
    print(f'  找到 {len(match_dirs)} 个比赛目录')
    
    for d in match_dirs:
        match_dir = os.path.join(data_dir, d)
        meta_path = os.path.join(match_dir, 'meta.json')
        if not os.path.exists(meta_path): continue
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except: continue
        
        match_num = meta.get('matchnum', '')
        if not match_num: continue
        
        o = {}
        
        # Step 1: 欧赔
        s1_path = os.path.join(match_dir, 'group01_europe', 'step1_europe_base.txt')
        if os.path.exists(s1_path):
            with open(s1_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '|' not in line: continue
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) < 8: continue
                    if parts[0] == '竞彩官方' and parts[1] != '-1':
                        o['jc_win'] = float(parts[4])
                        o['jc_draw'] = float(parts[5])
                        o['jc_loss'] = float(parts[6])
                        o['jc_panlu'] = parts[7][:3] if len(parts) > 7 else ''
                    elif parts[0] == '百家平均':
                        o['bj_win'] = float(parts[4])
                        o['bj_draw'] = float(parts[5])
                        o['bj_loss'] = float(parts[6])
                        o['bj_panlu'] = parts[7][:3] if len(parts) > 7 else ''
                    elif parts[0] == 'Interwetten':
                        o['iw_win'] = float(parts[4])
                        o['iw_draw'] = float(parts[5])
                        o['iw_loss'] = float(parts[6])
                        o['iw_panlu'] = parts[7][:3] if len(parts) > 7 else ''
        
        # Step 4: 让球
        s4_path = os.path.join(match_dir, 'group02_handicap', 'step4_handicap_base.txt')
        if os.path.exists(s4_path):
            with open(s4_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '|' not in line: continue
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) < 8: continue
                    if parts[0] == '竞彩官方':
                        o['rq_win'] = float(parts[5])
                        o['rq_draw'] = float(parts[6])
                        o['rq_loss'] = float(parts[7])
        
        # Step 6: 澳门亚盘
        s6_path = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
        if os.path.exists(s6_path):
            import re as re_mod
            with open(s6_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '澳门' not in line: continue
                    no_bracket = re_mod.sub(r'[（(].*?[）)]', '', line)
                    parts = [p.strip() for p in no_bracket.split('|') if p.strip()]
                    if len(parts) >= 3 and re_mod.search(r'[一-龥]', parts[2]):
                        o['macau'] = re_mod.sub(r'[⬆⬇➡▽△↑↓→←↔]', '', parts[2]).strip()
                    elif len(parts) >= 3:
                        raw = parts[-2] if len(parts) >= 2 else ''
                        o['macau'] = re_mod.sub(r'[\d\.⬆⬇➡▽△↑↓→←↔]', '', raw).strip()
                    break
            # Fallback to meta
            if not o.get('macau') and meta.get('macau_line'):
                o['macau'] = re_mod.sub(r'[⬆⬇➡▽△↑↓→←↔]', '', meta['macau_line']).strip()
        
        if o:
            odds[match_num] = o
    
    print(f'  提取到 {len(odds)} 场终盘赔率')
    return odds

# ===== Step 4: 读取预测 =====
def read_predictions(date_str):
    """从 task/<date>/*.md 报告文件提取竞彩预测和让球预测"""
    predictions = {}
    task_dir = os.path.join(WORKSPACE, 'tasks', date_str)
    if not os.path.exists(task_dir): return predictions
    
    for fname in os.listdir(task_dir):
        if not fname.endswith('.md') or fname.startswith('sunday'): continue
        
        m = re.match(r'^([周][一二三四五六日]\d+)[_]', fname)
        if not m: continue
        match_num = m.group(1)
        
        fpath = os.path.join(task_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except: continue
        
        pred = ''
        m2 = re.search(r'竞彩预测[\s:]*([^\n]+)', content)
        if m2: pred = m2.group(1).strip()
        if not pred:
            m2 = re.search(r'竞彩结论[\s:]*([^\n]+)', content)
            if m2: pred = m2.group(1).strip()
        if not pred:
            m2 = re.search(r'(?:推荐|建议)[\s:]*([^\n]+)', content)
            if m2: pred = m2.group(1).strip()
        
        rq_pred = ''
        m3 = re.search(r'让球预测[\s:]*([^\n|]+)', content)
        if m3: rq_pred = m3.group(1).strip()
        
        handicap = 0
        shou = re.search(r'受让(\d+(?:\.5)?)球', rq_pred)
        rang = re.search(r'(?:^|[^受])让(\d+(?:\.5)?)球', rq_pred)
        if shou: handicap = -float(shou.group(1))
        elif rang: handicap = float(rang.group(1))
        
        predictions[match_num] = {'prediction': pred, 'rqPred': rq_pred, 'handicap': handicap}
    
    print(f'  本地预测数据: {len(predictions)} 场')
    return predictions

# ===== Step 5: 更新 Notion =====
def notion_update(page_id, props):
    url = f'https://api.notion.com/v1/pages/{page_id}'
    body = {"properties": props}
    r = requests.patch(url, headers=NOTION_HEADERS, json=body, timeout=30)
    if r.status_code >= 400:
        raise Exception(f'HTTP {r.status_code}: {r.text[:200]}')
    return r.json()

def update_match(page_id, score, actual_result, is_correct, pred_str, handicap, rq_pred, odds_data):
    """Update Notion page with feedback data - mirrors feedback.js updateMatch()"""
    home_score = int(score.split(':')[0])
    away_score = int(score.split(':')[1])
    adj_home = home_score - handicap
    
    # 让球实际结果
    if adj_home > away_score: rq_actual = '胜'
    elif adj_home < away_score: rq_actual = '负'
    else: rq_actual = '平'
    
    # 让球预测是否正确
    pred_result = pred_to_result(pred_str)
    rq_is_correct = None
    if rq_pred and handicap != 0:
        rq_pred_result = pred_to_result(rq_pred)
        rq_is_correct = (rq_pred_result == rq_actual)
    elif rq_pred:
        rq_pred_result = pred_to_result(rq_pred)
        rq_is_correct = (rq_pred_result == actual_result)
    
    handicap_text = f'让{handicap}球' if handicap > 0 else (f'受让{abs(handicap)}球' if handicap < 0 else '平手')
    
    safe = lambda s: s.replace('\ufffd', '')
    pred_mark = '✅正确' if is_correct else '❌错误'
    summary = f'竞彩预测: {safe(pred_str)} → {actual_result} ({score}) {pred_mark}'
    if rq_pred:
        rq_mark = f' {("✅正确" if rq_is_correct else "❌错误")}' if rq_is_correct is not None else ''
        summary += f'\n让球预测: {safe(rq_pred)} → {handicap_text} {rq_actual} ({adj_home}:{away_score}){rq_mark}'
    
    props = {
        '实际比分': {'rich_text': [{'text': {'content': score or ''}}]},
        '实际结果': {'rich_text': [{'text': {'content': actual_result or ''}}]},
        '反馈日期': {'date': {'start': datetime.now().strftime('%Y-%m-%d')}},
        '反馈总结': {'rich_text': [{'text': {'content': summary}}]},
        '预测正确': {'checkbox': is_correct},
    }
    
    # 终盘赔率
    if odds_data:
        if odds_data.get('jc_win'): props['终盘竞彩欧赔胜'] = {'number': odds_data['jc_win']}
        if odds_data.get('jc_draw'): props['终盘竞彩欧赔平'] = {'number': odds_data['jc_draw']}
        if odds_data.get('jc_loss'): props['终盘竞彩欧赔负'] = {'number': odds_data['jc_loss']}
        if odds_data.get('bj_win'): props['终盘百家欧赔胜'] = {'number': odds_data['bj_win']}
        if odds_data.get('bj_draw'): props['终盘百家欧赔平'] = {'number': odds_data['bj_draw']}
        if odds_data.get('bj_loss'): props['终盘百家欧赔负'] = {'number': odds_data['bj_loss']}
        if odds_data.get('iw_win'): props['终盘Interwetten胜'] = {'number': odds_data['iw_win']}
        if odds_data.get('iw_draw'): props['终盘Interwetten平'] = {'number': odds_data['iw_draw']}
        if odds_data.get('iw_loss'): props['终盘Interwetten负'] = {'number': odds_data['iw_loss']}
        if odds_data.get('rq_win'): props['终盘让球指数胜'] = {'number': odds_data['rq_win']}
        if odds_data.get('rq_draw'): props['终盘让球指数平'] = {'number': odds_data['rq_draw']}
        if odds_data.get('rq_loss'): props['终盘让球指数负'] = {'number': odds_data['rq_loss']}
        if odds_data.get('macau'): props['终盘竞彩澳门亚盘'] = {'rich_text': [{'text': {'content': odds_data['macau']}}]}
        if odds_data.get('jc_panlu'): props['欧赔竞彩盘路'] = {'rich_text': [{'text': {'content': odds_data['jc_panlu']}}]}
        if odds_data.get('bj_panlu'): props['欧赔百家盘路'] = {'rich_text': [{'text': {'content': odds_data['bj_panlu']}}]}
        if odds_data.get('iw_panlu'): props['欧赔interwetten盘路'] = {'rich_text': [{'text': {'content': odds_data['iw_panlu']}}]}
        if odds_data.get('rq_panlu'): props['让球指数盘路'] = {'rich_text': [{'text': {'content': odds_data['rq_panlu']}}]}
        if odds_data.get('macau_panlu'): props['澳门亚盘盘路'] = {'rich_text': [{'text': {'content': odds_data['macau_panlu']}}]}
    
    if rq_pred:
        props['让球预测'] = {'rich_text': [{'text': {'content': rq_pred}}]}
    if rq_is_correct is not None:
        props['让球预测正确'] = {'checkbox': rq_is_correct}
    
    return notion_update(page_id, props)

# ===== 分组统计 =====
def generate_group_stats(notion_pages, match_results):
    groups = {}
    for page in notion_pages:
        props = page.get('properties', {})
        name_field = ''
        try:
            name_field = props.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
        except: pass
        name_m = re.match(r'^([周][一二三四五六日]\d+)', name_field)
        match_num = name_m.group(1) if name_m else ''
        
        notion_pred = ''
        try: notion_pred = props.get('竞彩预测', {}).get('rich_text', [{}])[0].get('plain_text', '')
        except: pass
        pred_result = pred_to_result(notion_pred)
        
        zj_text = ''
        try: zj_text = props.get('步26_庄家最看好', {}).get('rich_text', [{}])[0].get('plain_text', '')
        except: pass
        zj_result = None
        if '主胜' in zj_text: zj_result = '主胜'
        elif '客胜' in zj_text: zj_result = '客胜'
        elif '平局' in zj_text: zj_result = '平局'
        
        rq_pred = ''
        try: rq_pred = props.get('让球预测', {}).get('rich_text', [{}])[0].get('plain_text', '')
        except: pass
        rq_result = None
        rq_num_m = re.search(r'(受让\d+球|让[+-]?\d+(?:\.5)?球|平手)', rq_pred)
        rq_num_part = rq_num_m.group(1) if rq_num_m else ''
        if '让球主胜' in rq_pred or '让球胜' in rq_pred:
            rq_result = f'{rq_num_part} 主胜' if rq_num_part else '让球主胜'
        elif '让球客胜' in rq_pred:
            rq_result = f'{rq_num_part} 客胜' if rq_num_part else '让球客胜'
        elif '让球平' in rq_pred:
            rq_result = f'{rq_num_part} 平' if rq_num_part else '让球平'
        
        result = match_results.get(match_num)
        if not result: continue
        
        actual_result = '胜' if result['homeScore'] > result['awayScore'] else ('负' if result['homeScore'] < result['awayScore'] else '平')
        
        if not pred_result and not zj_result and not rq_result: continue
        group_key = f'{pred_result or "未知"}|{zj_result or "未知"}|{rq_result or "未知"}'
        
        if group_key not in groups:
            groups[group_key] = {'total': 0, '胜': 0, '平': 0, '负': 0}
        groups[group_key]['total'] += 1
        groups[group_key][actual_result] += 1
    
    return groups

# ===== 保存日志 =====
def save_log(target_date, notion_pages, updated, skipped, groups):
    log_file = os.path.join(DATA_DIR, f'feedback_{target_date}.json')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    sorted_groups = sorted(groups.items(), key=lambda x: -x[1]['total'])
    log_data = {
        'date': target_date,
        'total': len(notion_pages),
        'updated': updated,
        'skipped': skipped,
        'pending': len(notion_pages) - updated - skipped,
        'groups': dict(sorted_groups),
        'timestamp': datetime.now().isoformat()
    }
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    print(f'\n📄 日志已保存: {log_file}')

# ===== MAIN =====
def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    target_date = None
    for i, a in enumerate(args):
        if a == '--date' and i + 1 < len(args):
            target_date = args[i + 1]
    
    if target_date:
        prev = datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)
        target_date = prev.strftime('%Y-%m-%d')
    else:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f'\n📋 竞彩反馈机制 - {target_date}\n')
    
    # 1. 查询 Notion
    print('[1/4] 查询 Notion 比赛记录...')
    try:
        notion_pages = query_notion_matches(target_date)
    except Exception as e:
        print(f'  ❌ Notion 查询失败: {e}')
        print('  ⏳ 10秒后重试...')
        time.sleep(10)
        notion_pages = query_notion_matches(target_date)
    
    if not notion_pages:
        print(f'⚠️ Notion 中未找到 {target_date} 的比赛记录')
        print('提示: 请先运行竞彩流水线同步数据')
        return
    
    # 2. 获取赛果
    print('[2/4] 获取比赛结果...')
    match_results = fetch_match_results(target_date)
    
    # 存档比分
    archive_file = os.path.join(DATA_DIR, 'scores_archive.json')
    archive = {}
    if os.path.exists(archive_file):
        try:
            with open(archive_file, 'r', encoding='utf-8') as f:
                archive = json.load(f)
        except: pass
    if match_results:
        archive[target_date] = match_results
        os.makedirs(os.path.dirname(archive_file), exist_ok=True)
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive, f, ensure_ascii=False, indent=2)
        print(f'📦 比分已存档: {archive_file} ({len(match_results)} 场)')
    
    # 终盘赔率
    print('[3/4] 获取终盘赔率数据...')
    final_odds = fetch_final_odds(target_date)
    
    # 读取预测
    print('读取预测数据...')
    predictions = read_predictions(target_date)
    
    # 3. 更新 Notion
    print('\n[3/4] 更新 Notion 记录...\n')
    updated = 0
    skipped = 0
    
    for page in notion_pages:
        props = page.get('properties', {})
        name_field = ''
        try:
            name_field = props.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
        except: pass
        
        name_m = re.match(r'^([周][一二三四五六日]\d+)', name_field)
        match_num = name_m.group(1) if name_m else ''
        
        team_m = re.search(r'\d+\s*\S+\s*(.+?)\s*vs\s*(.+)$', name_field)
        home = team_m.group(1).strip() if team_m else ''
        away = team_m.group(2).strip() if team_m else ''
        
        notion_pred = ''
        try: notion_pred = props.get('竞彩预测', {}).get('rich_text', [{}])[0].get('plain_text', '')
        except: pass
        
        match_odds = final_odds.get(match_num)
        
        # Write odds first
        if match_odds:
            try:
                odd_props = {}
                if match_odds.get('jc_win'): odd_props['终盘竞彩欧赔胜'] = {'number': match_odds['jc_win']}
                if match_odds.get('jc_draw'): odd_props['终盘竞彩欧赔平'] = {'number': match_odds['jc_draw']}
                if match_odds.get('jc_loss'): odd_props['终盘竞彩欧赔负'] = {'number': match_odds['jc_loss']}
                if match_odds.get('bj_win'): odd_props['终盘百家欧赔胜'] = {'number': match_odds['bj_win']}
                if match_odds.get('bj_draw'): odd_props['终盘百家欧赔平'] = {'number': match_odds['bj_draw']}
                if match_odds.get('bj_loss'): odd_props['终盘百家欧赔负'] = {'number': match_odds['bj_loss']}
                if match_odds.get('iw_win'): odd_props['终盘Interwetten胜'] = {'number': match_odds['iw_win']}
                if match_odds.get('iw_draw'): odd_props['终盘Interwetten平'] = {'number': match_odds['iw_draw']}
                if match_odds.get('iw_loss'): odd_props['终盘Interwetten负'] = {'number': match_odds['iw_loss']}
                if match_odds.get('rq_win'): odd_props['终盘让球指数胜'] = {'number': match_odds['rq_win']}
                if match_odds.get('rq_draw'): odd_props['终盘让球指数平'] = {'number': match_odds['rq_draw']}
                if match_odds.get('rq_loss'): odd_props['终盘让球指数负'] = {'number': match_odds['rq_loss']}
                if match_odds.get('macau'): odd_props['终盘竞彩澳门亚盘'] = {'rich_text': [{'text': {'content': match_odds['macau']}}]}
                notion_update(page['id'], odd_props)
            except Exception as e:
                print(f'  ⚠️ 赔率写入失败: {e}')
        
        pred = notion_pred or ''
        pred_result = pred_to_result(pred)
        
        rq_pred = ''
        try: rq_pred = props.get('让球预测', {}).get('rich_text', [{}])[0].get('plain_text', '')
        except: pass
        
        handicap = 0
        shou = re.search(r'受让(\d+(?:\.5)?)球', rq_pred)
        rang = re.search(r'(?:^|[^受])让(\d+(?:\.5)?)球', rq_pred)
        if shou: handicap = -float(shou.group(1))
        elif rang: handicap = float(rang.group(1))
        
        result = match_results.get(match_num)
        
        if not result:
            print(f'📝 {match_num} {home} vs {away}')
            print(f'   预测: {pred or "无"}')
            print(f'   状态: 等待赛果公布\n')
            continue
        
        score = f'{result["homeScore"]}:{result["awayScore"]}'
        if result['homeScore'] > result['awayScore']: actual_result = '胜'
        elif result['homeScore'] < result['awayScore']: actual_result = '负'
        else: actual_result = '平'
        
        is_correct = (pred_result == actual_result)
        
        print(f'📝 {match_num} {home} vs {away}')
        print(f'   比分: {score} ({actual_result})')
        print(f'   预测: {pred} → {pred_result or "未知"}')
        print(f'   正确: {"✅" if is_correct else "❌"}')
        
        try:
            match_final_odds = final_odds.get(match_num)
            update_match(page['id'], score, actual_result, is_correct, pred, handicap, rq_pred, match_final_odds)
            print(f'   ✅ 已更新 Notion')
            if match_final_odds:
                print(f'   终盘欧赔: {match_final_odds.get("jc_win", "?")} / {match_final_odds.get("jc_draw", "?")} / {match_final_odds.get("jc_loss", "?")}')
            updated += 1
        except Exception as e:
            print(f'   ❌ 更新失败: {e}')
        print()
    
    print(f'\n✅ 反馈检查完成')
    print(f'   已更新: {updated}')
    print(f'   已跳过: {skipped}')
    print(f'   待查: {len(notion_pages) - updated - skipped}')
    
    # 4. 分组统计
    print('\n[4/5] 生成分组统计...')
    groups = generate_group_stats(notion_pages, match_results)
    
    print('\n📊 分组统计:')
    sorted_groups = sorted(groups.items(), key=lambda x: -x[1]['total'])
    for key, stats in sorted_groups:
        parts = key.split('|')
        print(f"| {parts[0]} | {parts[1]} | {parts[2]} | {stats['total']} | {stats['胜']} | {stats['平']} | {stats['负']} |")
    
    total_wins = sum(s['胜'] for s in groups.values())
    total_draws = sum(s['平'] for s in groups.values())
    total_losses = sum(s['负'] for s in groups.values())
    total = total_wins + total_draws + total_losses
    print(f'\n{total}场合计：胜{total_wins} 平{total_draws} 负{total_losses}')
    print('✅ match页面 + 每日分组 + 历史汇总 已跳过（26步数据库已用于存储26步分析内容）')
    
    # 5. 尝试运行 sync_summary.js (通过 WSL bash)
    print('\n[5/5] 全量刷新历史汇总...')
    try:
        import subprocess
        # Try via WSL bash since Windows Node can't do network
        result = subprocess.run(
            ['bash', '-c', 'cd /mnt/c/Users/lianjie/.openclaw/workspace/jingcai && python3 -c "print(\'sync_summary skipped - Node not available\')"'],
            capture_output=True, text=True, timeout=30
        )
        print(f'   sync_summary.js skipped (Windows Node network unavailable)')
        print('✅ 历史汇总已跳过（需修复 Windows Node 网络后单独运行）')
    except Exception as e:
        print(f'⚠️ 历史汇总刷新跳过: {e}')
    
    # 保存日志
    save_log(target_date, notion_pages, updated, skipped, groups)


if __name__ == '__main__':
    main()
