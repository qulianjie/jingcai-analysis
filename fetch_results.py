# -*- coding: utf-8 -*-
"""
批量拉取赛果 - 从 500.com 获取历史赛果
用法: python fetch_results.py [--date 2026-04-24] [--all]
"""
import os, sys, re, json
from datetime import datetime, timedelta
import requests

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def fetch_results_for_date(date_str):
    """从 500.com 拉取指定日期的赛果"""
    url = f'https://trade.500.com/jczq/?playid=271&g=2&date={date_str}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        session.get('https://trade.500.com/', timeout=10)
        resp = session.get(url, timeout=15)
        html = resp.content.decode('gbk', errors='ignore')
    except Exception as e:
        log('ERR', '获取失败: {}'.format(e))
        return {}
    
    results = {}
    
    # 解析 HTML 表格，提取赛果
    # 从 <tr data-fixtureid="..."> 块中提取
    # 比分在 <a class="score">X:X</a> 里
    # matchnum 在 data-matchnum 里（如“周日001”）
    # 需要提取完整 <tr>...</tr>
    tr_blocks = re.findall(r'<tr[^>]*data-fixtureid="[^"]*"[^>]*>.*?</tr>', html, re.DOTALL)
    
    for tr in tr_blocks:
        # 提取竞彩编号（从 data-matchnum 提取数字）
        mn = re.search(r'data-matchnum="[^\"]*(\d{3})"', tr)
        if not mn:
            continue
        match_num = mn.group(1)
        
        # 提取比分
        sm = re.search(r'<a class="score"[^>]*>(\d+:\d+)</a>', tr)
        if not sm:
            continue
        score = sm.group(1)
        
        # 从比分推导胜平负
        parts = score.split(':')
        if len(parts) == 2:
            try:
                h, a = int(parts[0]), int(parts[1])
                if h > a: result = '胜'
                elif h == a: result = '平'
                else: result = '负'
            except:
                result = '待查'
        else:
            result = '待查'
        
        results[match_num] = {
            'score': score,
            'result': result,
        }
    
    return results

def fetch_results_from_reports(date_str):
    """从报告文件中提取赛果（如果有的话）"""
    task_dir = os.path.join(SCRIPT_DIR, 'tasks', date_str)
    if not os.path.exists(task_dir):
        return {}
    
    results = {}
    
    # 从报告文件名和报告中提取
    for f in os.listdir(task_dir):
        if not f.endswith('.md'):
            continue
        
        content = ''
        try:
            with open(os.path.join(task_dir, f), 'r', encoding='utf-8') as fh:
                content = fh.read()
        except:
            continue
        
        # 从文件名提取match_num
        mn_match = re.search(r'(\d{3})', f)
        if not mn_match:
            continue
        mn = mn_match.group(1)
        
        # 从报告中提取比分和结果
        score_match = re.search(r'比分[：:]\s*(\d+[:：]\d+)', content)
        result_match = re.search(r'赛果[：:]\s*([胜负平待查]+)', content)
        
        if score_match:
            score = score_match.group(1).replace('：', ':')
            parts = score.split(':')
            if len(parts) == 2:
                try:
                    h, a = int(parts[0]), int(parts[1])
                    if h > a: result = '胜'
                    elif h == a: result = '平'
                    else: result = '负'
                except:
                    result = result_match.group(1) if result_match else '待查'
            else:
                result = result_match.group(1) if result_match else '待查'
        else:
            score = '待查'
            result = result_match.group(1) if result_match else '待查'
        
        results[mn] = {
            'score': score,
            'result': result,
        }
    
    return results

def main():
    log('START', '批量拉取赛果')
    
    dates_to_fetch = []
    
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        # 拉取所有有报告的日期
        tasks_dir = os.path.join(SCRIPT_DIR, 'tasks')
        if os.path.exists(tasks_dir):
            for d in sorted(os.listdir(tasks_dir)):
                if re.match(r'\d{4}-\d{2}-\d{2}', d):
                    dates_to_fetch.append(d)
    elif len(sys.argv) > 1 and sys.argv[1] == '--date':
        if len(sys.argv) > 2:
            dates_to_fetch = [sys.argv[2]]
    else:
        # 默认拉取最近7天
        today = datetime.now()
        for i in range(7):
            dates_to_fetch.append((today - timedelta(days=i)).strftime('%Y-%m-%d'))
    
    log('INFO', '待处理日期: {}'.format(', '.join(dates_to_fetch)))
    
    # 加载已有赛果
    all_results = {}
    for date_str in dates_to_fetch:
        rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str))
        if os.path.exists(rf):
            try:
                with open(rf, 'r', encoding='utf-8') as f:
                    all_results[date_str] = json.load(f).get(date_str, {})
            except:
                all_results[date_str] = {}
    
    # 拉取新赛果
    for date_str in dates_to_fetch:
        log('DATE', '处理 {}'.format(date_str))
        
        # 1. 尝试从sporttery拉取
        results = fetch_results_for_date(date_str)
        
        # 2. 如果拉取失败，从报告提取
        if not results:
            log('INFO', '从报告提取赛果')
            results = fetch_results_from_reports(date_str)
        
        if results:
            log('OK', '{}: {} 场'.format(date_str, len(results)))
            all_results[date_str] = results
            
            # 保存
            rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str))
            with open(rf, 'w', encoding='utf-8') as f:
                json.dump({date_str: results}, f, ensure_ascii=False, indent=2)
        else:
            log('WARN', '{}: 未找到赛果'.format(date_str))
    
    log('DONE', '全部完成')

if __name__ == '__main__':
    main()
