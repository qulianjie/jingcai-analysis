#!/usr/bin/env python3
"""Daily feedback pipeline for jingcai (竞彩) - Python replacement for feedback.js.
Uses curl via notion_curl.py for all HTTP (bypasses Node.js TLS issues on Windows)."""
import json, os, re, subprocess, sys, glob, html
from datetime import datetime, timedelta

BASE = '/mnt/c/Users/lianjie/.openclaw/workspace/jingcai'
DATA_DIR = os.path.join(BASE, '..', 'data', 'jingcai')

def curl(action, *args):
    """Call notion_curl.py and return parsed result."""
    cmd = ['python3', os.path.join(BASE, 'notion_curl.py'), action] + list(args)
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    out = r.stdout.decode('utf-8', errors='replace')
    if r.returncode != 0:
        return {'error': r.stderr.decode()[:200]}
    try:
        return json.loads(out)
    except:
        return {'error': 'parse fail', 'raw': out[:200]}


def query_notion(date_str):
    """Query Notion for matches on a given date."""
    flt = json.dumps({
        "filter": {"and": [{"property": "比赛日期", "date": {"equals": date_str}}]},
        "page_size": 100
    }, ensure_ascii=False)
    r = curl('query-db', '35491ad7-17ba-81cc-aa04-ce53f7234e17', flt)
    pages = r.get('json', {}).get('results', []) if r.get('json') else []
    return pages


def get_prop(props, name, field='rich_text', idx=0, sub='text', sub2='content'):
    """Safely extract a Notion property value."""
    p = props.get(name, {})
    val = p.get(field)
    if isinstance(val, list) and len(val) > idx:
        if sub:
            return val[idx].get(sub, {}).get(sub2, '')
        return val[idx]
    if field == 'number':
        return p.get('number')
    if field == 'checkbox':
        return p.get('checkbox')
    if field == 'select':
        s = p.get('select')
        return s.get('name', '') if s else ''
    if field == 'title':
        t = p.get('title', [])
        return t[0].get('plain_text', '') if t else ''
    return ''


def prediction_to_result(pred):
    """Parse prediction string to result (胜/平/负)."""
    if '主胜' in pred: return '胜'
    if '客胜' in pred: return '负'
    if '平局' in pred or pred.strip() == '平': return '平'
    return ''


def notion_patch(page_id, props):
    """Patch a Notion page with properties."""
    r = curl('patch-page', page_id, json.dumps({'properties': props}, ensure_ascii=False))
    return r.get('status') in (200, 201, 204)


def get_final_odds(target_date):
    """Extract final odds from step146_extractor output files."""
    odds = {}
    task_dir = os.path.join(BASE, 'tasks', target_date)
    data_dir = os.path.join(task_dir, 'data')
    match_dirs = []
    if os.path.isdir(data_dir):
        match_dirs = [d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))]
    
    # Also check legacy _tmp_odds
    if not match_dirs:
        legacy = os.path.join(data_dir, '_tmp_odds') if data_dir else ''
        if legacy and os.path.isdir(legacy):
            match_dirs = [d for d in os.listdir(legacy) if os.path.isdir(os.path.join(legacy, d))]
            data_dir = legacy
    
    for d in match_dirs:
        meta_path = os.path.join(data_dir, d, 'meta.json')
        if not os.path.exists(meta_path): continue
        meta = json.load(open(meta_path, 'r'))
        mn = meta.get('matchnum', '')
        if not mn: continue
        
        match_dir = os.path.join(data_dir, d)
        try:
            subprocess.run(['python3', 'step146_extractor.py', match_dir], cwd=BASE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        except:
            pass
        
        o = {}
        s1 = os.path.join(match_dir, 'group01_europe', 'step1_europe_base.txt')
        s4 = os.path.join(match_dir, 'group02_handicap', 'step4_handicap_base.txt')
        s6 = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
        
        if os.path.exists(s1):
            for line in open(s1, 'r'):
                if '|' not in line: continue
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) < 8: continue
                if parts[0] == '竞彩官方' and parts[1] != '-1':
                    o['jc_win'] = float(parts[4])
                    o['jc_draw'] = float(parts[5])
                    o['jc_loss'] = float(parts[6])
                if parts[0] == '百家平均':
                    o['bj_win'] = float(parts[4])
                    o['bj_draw'] = float(parts[5])
                    o['bj_loss'] = float(parts[6])
                if parts[0] == 'Interwetten':
                    o['iw_win'] = float(parts[4])
                    o['iw_draw'] = float(parts[5])
                    o['iw_loss'] = float(parts[6])
        
        if os.path.exists(s4):
            for line in open(s4, 'r'):
                if '|' not in line: continue
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) < 8: continue
                if parts[0] == '竞彩官方':
                    o['rq_win'] = float(parts[5])
                    o['rq_draw'] = float(parts[6])
                    o['rq_loss'] = float(parts[7])
        
        if os.path.exists(s6):
            for line in open(s6, 'r'):
                if '澳门' not in line: continue
                nobracket = re.sub(r'[（(].*?[）)]', '', line)
                pts = [p.strip() for p in nobracket.split('|') if p.strip()]
                if len(pts) >= 3 and re.search(r'[\u4e00-\u9fa5]', pts[-1]):
                    o['macau'] = re.sub(r'[⬆⬇➡▽△↑↓→←↔]', '', pts[-1]).strip()
                break
        
        if o:
            odds[mn] = o
    
    return odds


def get_predictions(target_date):
    """Extract predictions from local markdown files."""
    predictions = {}
    task_dir = os.path.join(BASE, 'tasks', target_date)
    if not os.path.isdir(task_dir): return predictions
    
    for fname in os.listdir(task_dir):
        if not fname.endswith('.md') or fname.startswith('sunday'): continue
        m = re.match(r'^(周[一二三四五六日]\d+)[_.]', fname)
        if not m: continue
        mn = m.group(1)
        content = open(os.path.join(task_dir, fname), 'r').read()
        
        pred = ''
        for pat in ['竞彩预测', '竞彩结论', '推荐', '建议']:
            m2 = re.search(r'%s[:：\s]*([^\n]+)' % pat, content)
            if m2: pred = m2.group(1).strip(); break
        
        rq_pred = ''
        m3 = re.search(r'让球预测[:：\s]*([^\n|]+)', content)
        if m3: rq_pred = m3.group(1).strip()
        
        handicap = 0
        shou = re.search(r'受让([\d.]+)球', rq_pred)
        rang = re.search(r'(?:^|[^受])让([\d.]+)球', rq_pred)
        if shou: handicap = -float(shou.group(1))
        elif rang: handicap = float(rang.group(1))
        
        if pred:
            predictions[mn] = {'prediction': pred, 'rqPred': rq_pred, 'handicap': handicap}
    
    return predictions


def get_match_results(date_str):
    """Fetch match results from 500.com.
    
    The 500.com page lists matches for the given date. Completed matches
    have scores embedded in the team text (e.g., "拉赫蒂1:1瓦萨")
    while unplayed matches show "VS" between team names.
    """
    r = curl('fetch-500', date_str)
    body = r.get('body', '')
    if not body:
        return {}
    
    results = {}
    # Find all match rows
    tr_pattern = re.compile(r'<tr[^>]*class="[^"]*bet-tb-tr[^"]*"[^>]*>(.*?)</tr>', re.DOTALL)
    
    for tr_match in tr_pattern.finditer(body):
        tr_html = tr_match.group(0)
        
        # Extract match number
        mn_m = re.search(r'data-matchnum="([^"]+)"', tr_html)
        if not mn_m: continue
        match_num = mn_m.group(1).strip()
        
        # Extract team text from td-team
        team_td = re.search(r'<td[^>]*class="[^"]*td-team[^"]*"[^>]*>(.*?)</td>', tr_html, re.DOTALL)
        if not team_td: continue
        team_text = re.sub(r'<[^>]*>', '', team_td.group(1)).strip()
        team_text = html.unescape(team_text)
        
        # Completed matches have scores instead of "VS"
        if 'VS' not in team_text:
            sc = re.search(r'(\d+):(\d+)', team_text)
            if sc:
                hs, as_ = int(sc.group(1)), int(sc.group(2))
                if hs <= 20 and as_ <= 20:
                    results[match_num] = {'homeScore': hs, 'awayScore': as_}
    
    return results


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    prev_day = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    target_date = prev_day
    
    print("\n📋 竞彩反馈机制 - %s\n" % target_date)
    
    # 1. Query Notion
    print("[1/4] 查询 Notion 比赛记录...")
    pages = query_notion(target_date)
    if not pages:
        import time
        time.sleep(3)
        pages = query_notion(target_date)
    
    if not pages:
        print("⚠️ Notion 中未找到 %s 的比赛记录" % target_date)
        print("提示: 请先运行竞彩流水线同步数据")
        return
    
    print("找到 %d 场比赛\n" % len(pages))
    
    # 2. Fetch scores
    print("[2/4] 获取比赛结果...")
    match_results = get_match_results(target_date)
    if not match_results:
        print("⚠️ 未能获取赛果（500.com 可能暂无数据或连接异常）")
    else:
        print("获取到 %d 场赛果" % len(match_results))
        for mn, r in match_results.items():
            print("  %s: %d:%d" % (mn, r['homeScore'], r['awayScore']))
    
    # Archive scores
    if match_results:
        os.makedirs(DATA_DIR, exist_ok=True)
        archive_file = os.path.join(DATA_DIR, 'scores_archive.json')
        archive = {}
        if os.path.exists(archive_file):
            try: archive = json.load(open(archive_file, 'r'))
            except: pass
        if target_date not in archive:
            archive[target_date] = {}
        archive[target_date].update({k: '%d:%d' % (v['homeScore'], v['awayScore']) for k, v in match_results.items()})
        json.dump(archive, open(archive_file, 'w'), ensure_ascii=False, indent=2)
        print("📦 比分已存档")
    
    # Get final odds
    final_odds = get_final_odds(target_date)
    print("获取到 %d 场终盘赔率" % len(final_odds))
    
    # Get predictions
    predictions = get_predictions(target_date)
    print("本地预测数据: %d 场" % len(predictions))
    
    # 3. Update Notion
    print("\n[3/4] 更新 Notion 记录...\n")
    
    updated = 0
    skipped = 0
    results_table = []
    
    for page in pages:
        props = page.get('properties', {})
        name = get_prop(props, 'Name', 'title')
        nm = re.match(r'^(周[一二三四五六日]\d+)', name)
        match_num = nm.group(1) if nm else ''
        
        team_m = re.search(r'\d+\s*\S+\s*(.+?)\s*vs\s*(.+)$', name)
        home = team_m.group(1).strip() if team_m else ''
        away = team_m.group(2).strip() if team_m else ''
        
        notion_pred = get_prop(props, '竞彩预测')
        pred_str = notion_pred or ''
        pred_result = prediction_to_result(pred_str)
        
        rq_pred = get_prop(props, '让球预测')
        handicap = 0
        shou = re.search(r'受让([\d.]+)球', rq_pred)
        rang = re.search(r'(?:^|[^受])让([\d.]+)球', rq_pred)
        if shou: handicap = -float(shou.group(1))
        elif rang: handicap = float(rang.group(1))
        
        result = match_results.get(match_num, {})
        pid = page.get('id', '')
        
        # First update odds if available
        match_odds = final_odds.get(match_num, {})
        if match_odds:
            odd_props = {}
            for k, v in [('jc_win', '终盘竞彩欧赔胜'), ('jc_draw', '终盘竞彩欧赔平'), ('jc_loss', '终盘竞彩欧赔负'),
                          ('bj_win', '终盘百家欧赔胜'), ('bj_draw', '终盘百家欧赔平'), ('bj_loss', '终盘百家欧赔负'),
                          ('iw_win', '终盘Interwetten胜'), ('iw_draw', '终盘Interwetten平'), ('iw_loss', '终盘Interwetten负'),
                          ('rq_win', '终盘让球指数胜'), ('rq_draw', '终盘让球指数平'), ('rq_loss', '终盘让球指数负')]:
                if k in match_odds and match_odds[k]:
                    odd_props[v] = {'number': match_odds[k]}
            if 'macau' in match_odds:
                odd_props['终盘竞彩澳门亚盘'] = {'rich_text': [{'text': {'content': match_odds['macau']}}]}
            if odd_props:
                notion_patch(pid, odd_props)
        
        if not result:
            print("📝 %s %s vs %s" % (match_num, home, away))
            print("   预测: %s" % (pred_str or '无'))
            print("   状态: 等待赛果公布\n")
            continue
        
        score = "%d:%d" % (result['homeScore'], result['awayScore'])
        if result['homeScore'] > result['awayScore']:
            actual = '胜'
        elif result['homeScore'] < result['awayScore']:
            actual = '负'
        else:
            actual = '平'
        
        is_correct = pred_result == actual
        
        # Calculate rq result
        adj_home = result['homeScore'] - handicap
        if adj_home > result['awayScore']:
            rq_actual = '胜'
        elif adj_home < result['awayScore']:
            rq_actual = '负'
        else:
            rq_actual = '平'
        
        rq_pred_result = prediction_to_result(rq_pred)
        rq_is_correct = rq_pred_result == rq_actual if rq_pred_result else None
        
        # Build summary
        pred_mark = '✅正确' if is_correct else '❌错误'
        rq_mark = ''
        if rq_is_correct is True:
            rq_mark = ' ✅正确'
        elif rq_is_correct is False:
            rq_mark = ' ❌错误'
        
        handicap_text = ''
        if handicap > 0: handicap_text = '让%d球' % handicap
        elif handicap < 0: handicap_text = '受让%d球' % abs(handicap)
        else: handicap_text = '平手'
        
        summary = '竞彩预测: %s → %s (%s) %s' % (pred_str, actual, score, pred_mark)
        if rq_pred:
            summary += '\n让球预测: %s → %s %s (%d:%d)%s' % (rq_pred, handicap_text, rq_actual, adj_home, result['awayScore'], rq_mark)
        
        # Update Notion
        update_props = {
            '实际比分': {'rich_text': [{'text': {'content': score}}]},
            '实际结果': {'rich_text': [{'text': {'content': actual}}]},
            '反馈日期': {'date': {'start': today}},
            '反馈总结': {'rich_text': [{'text': {'content': summary}}]},
            '预测正确': {'checkbox': is_correct},
        }
        if rq_pred:
            update_props['让球预测正确'] = {'checkbox': rq_is_correct if rq_is_correct is not None else False}
        
        ok = notion_patch(pid, update_props)
        
        print("📝 %s %s vs %s" % (match_num, home, away))
        print("   比分: %s (%s)" % (score, actual))
        print("   预测: %s → %s" % (pred_str, pred_result or '未知'))
        print("   正确: %s" % ('✅' if is_correct else '❌'))
        if ok:
            print("   ✅ 已更新 Notion")
        else:
            print("   ⚠️ 更新失败")
        if match_odds:
            print("   终盘欧赔: %s / %s / %s" % (
                match_odds.get('jc_win', '-'), match_odds.get('jc_draw', '-'), match_odds.get('jc_loss', '-')))
        print("")
        
        results_table.append({
            'match': match_num,
            'teams': '%s vs %s' % (home, away),
            'score': score,
            'actual': actual,
            'prediction': pred_str,
            'pred_result': pred_result,
            'correct': is_correct,
            'rq_prediction': rq_pred,
            'rq_correct': rq_is_correct,
        })
        updated += 1
    
    total = len(results_table)
    correct_count = sum(1 for r in results_table if r['correct'])
    wrong_count = total - correct_count
    rq_correct = sum(1 for r in results_table if r['rq_correct'] is True)
    rq_wrong = sum(1 for r in results_table if r['rq_correct'] is False)
    total_rq = rq_correct + rq_wrong
    
    print("\n✅ 反馈检查完成")
    print("   已更新: %d" % updated)
    print("   待查: %d" % (len(pages) - updated))
    
    # Print statistics
    print("\n" + "="*60)
    print("📊 准确率统计")
    print("="*60)
    
    if total > 0:
        acc = correct_count / total * 100
        print("\n🏆 竞彩预测:")
        for r in results_table:
            mark = '✅' if r['correct'] else '❌'
            print("  %s %s → %s (实际%s) %s" % (r['match'], r['prediction'][:25].ljust(25), r['pred_result'], r['actual'], mark))
        print("\n  总计: %d 正确, %d 错误, 准确率: %.1f%% (%d/%d)" % (correct_count, wrong_count, acc, correct_count, total))
    
    if total_rq > 0:
        rq_acc = rq_correct / total_rq * 100
        print("\n🏆 让球预测:")
        for r in results_table:
            if r.get('rq_prediction'):
                mark = '✅' if r['rq_correct'] else '❌'
                print("  %s %s %s" % (r['match'], r['rq_prediction'][:30].ljust(30), mark))
        print("\n  总计: %d 正确, %d 错误, 准确率: %.1f%% (%d/%d)" % (rq_correct, rq_wrong, rq_acc, rq_correct, total_rq))
    
    # Top signals analysis
    print("\n" + "="*60)
    print("🔍 TOP 信号分析")
    print("="*60)
    
    if total > 0:
        correct_preds = [r for r in results_table if r['correct']]
        wrong_preds = [r for r in results_table if not r['correct']]
        
        if correct_preds:
            print("\n✅ 预测正确的比赛:")
            for r in correct_preds:
                print("  %s %s → %s (比分 %s)" % (r['match'], r['teams'].ljust(25), r['actual'], r['score']))
        
        if wrong_preds:
            print("\n❌ 预测错误的比赛:")
            for r in wrong_preds:
                print("  %s %s → 预测%s 实际%s (比分 %s)" % (r['match'], r['teams'].ljust(25), r['pred_result'], r['actual'], r['score']))
    
    print("\n📄 日志已写入 Notion（反馈日期: %s）" % today)

if __name__ == '__main__':
    main()
