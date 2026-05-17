# -*- coding: utf-8 -*-
"""
竞彩反馈Notion同步器 - 把批量反馈结果更新到Notion
用法: python notion_feedback_sync.py 2026-05-02 2026-05-03 2026-05-04
"""
import os, sys, json, re, requests, time
from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

NOTION_API_KEY = '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'
DATABASE_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

H = {
    'Authorization': 'Bearer ' + NOTION_API_KEY,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

def notion_get(url, timeout=30, retries=3):
    """带重试的Notion GET"""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=H, timeout=timeout)
            return r
        except requests.exceptions.ReadTimeout:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise

def notion_post(url, json=None, timeout=30, retries=3):
    """带重试的Notion POST"""
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=H, json=json, timeout=timeout)
            return r
        except requests.exceptions.ReadTimeout:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise

def notion_patch(url, json=None, timeout=30, retries=3):
    """带重试的Notion PATCH"""
    for attempt in range(retries):
        try:
            r = requests.patch(url, headers=H, json=json, timeout=timeout)
            return r
        except requests.exceptions.ReadTimeout:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def ensure_feedback_fields():
    """确保Notion数据库有反馈相关字段"""
    fields_to_add = {
        '实际比分': {'rich_text': {}},
        '实际结果': {'rich_text': {}},
        '预测正确': {'checkbox': {}},
        '让球预测正确': {'checkbox': {}},
        '反馈日期': {'date': {}},
        '反馈总结': {'rich_text': {}},
    }
    
    # Check existing fields
    r = notion_get('https://api.notion.com/v1/databases/' + DATABASE_ID)
    db = r.json()
    existing = set(db.get('properties', {}).keys())
    
    new_fields = {k: v for k, v in fields_to_add.items() if k not in existing}
    
    if new_fields:
        log('INFO', '添加反馈字段: {}'.format(', '.join(new_fields.keys())))
        r = notion_patch('https://api.notion.com/v1/databases/' + DATABASE_ID,
                          json={'properties': new_fields})
        if r.status_code == 200:
            log('OK', '已添加 {} 个字段'.format(len(new_fields)))
        else:
            log('ERR', '添加字段失败: {}'.format(r.text[:200]))
    else:
        log('INFO', '反馈字段已存在')

def get_notion_pages_by_date(date_str):
    """获取某天的所有Notion页面"""
    body = {
        'page_size': 100,
        'filter': {'property': '比赛日期', 'date': {'equals': date_str}}
    }
    r = notion_post('https://api.notion.com/v1/databases/' + DATABASE_ID + '/query',
                     json=body)
    result = r.json()
    return result.get('results', [])

def extract_prediction_from_report(md_path):
    """从最终报告提取预测和信心"""
    if not os.path.exists(md_path):
        return None
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取让球预测（主预测）
    rq_pred = ''
    rq_conf = 0
    rq_m = re.search(r'\*\*让球预测\*\*\s*\|\s*([^\|\n]+)', content)
    if rq_m:
        rq_text = rq_m.group(1).strip()
        pred_m = re.match(r'让球([胜负平])', rq_text)
        if pred_m:
            rq_pred = pred_m.group(1)
        conf_m = re.search(r'(\d+)%', rq_text)
        if conf_m:
            rq_conf = int(conf_m.group(1)) / 100.0
    
    # 提取竞彩预测（备用）
    pred = ''
    conf = 0
    m = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|\n]+)', content)
    if m:
        pred = m.group(1).strip()
    m = re.search(r'\*\*信心\*\*\s*\|\s*(\d+)%', content)
    if m:
        conf = int(m.group(1)) / 100.0
    
    # 提取比赛对阵
    home = ''
    away = ''
    m = re.search(r'(\S+)\s*vs\s*(\S+)', content[:500])
    if m:
        home = m.group(1).strip()
        away = m.group(2).strip()
    
    return {
        'pred': pred or rq_pred,
        'rq_pred': rq_pred,
        'conf': conf or rq_conf,
        'rq_conf': rq_conf,
        'home': home,
        'away': away,
    }

def get_result_converter():
    """获取竞彩结果转换表（胜/平/负 -> 胜平负）"""
    return {'胜': '胜', '平': '平', '负': '负'}

def main():
    if len(sys.argv) < 2:
        print('用法: python notion_feedback_sync.py <date1> [date2] ...')
        print('示例: python notion_feedback_sync.py 2026-05-02 2026-05-03 2026-05-04')
        sys.exit(1)
    
    log('START', '竞彩反馈Notion同步')
    
    # Step 1: Ensure feedback fields exist
    ensure_feedback_fields()
    
    # Step 2: Load feedback data
    feedback_file = os.path.join(SCRIPT_DIR, 'learnings/feedback.json')
    if not os.path.exists(feedback_file):
        log('ERR', '反馈文件不存在: {}'.format(feedback_file))
        sys.exit(1)
    
    with open(feedback_file, 'r', encoding='utf-8') as f:
        feedback_all = json.load(f)
    
    # Step 3: Load results files
    results_files = {}
    for date_str in sys.argv[1:]:
        rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str))
        if os.path.exists(rf):
            with open(rf, 'r', encoding='utf-8') as f:
                results_files[date_str] = json.load(f).get(date_str, {})
        else:
            log('WARN', '结果文件不存在: {}'.format(rf))
    
    # Step 4: Process each date
    total_updated = 0
    total_not_found = 0
    
    for date_str in sys.argv[1:]:
        log('DATE', '处理 {}'.format(date_str))
        
        # Get Notion pages for this date
        pages = get_notion_pages_by_date(date_str)
        log('INFO', 'Notion中找到 {} 场'.format(len(pages)))
        
        # Build match lookup
        page_lookup = {}
        for p in pages:
            props = p.get('properties', {})
            match_num = ''
            match_name = ''
            
            for pname, pval in props.items():
                if pval.get('type') == 'title':
                    titles = pval.get('title', [])
                    if titles:
                        match_name = titles[0].get('plain_text', '')
                elif pname == '竞彩编号':
                    rt = pval.get('rich_text', [])
                    if rt:
                        match_num = rt[0].get('plain_text', '')
            
            if match_num:
                page_lookup[match_num] = {'id': p['id'], 'name': match_name}
            elif match_name:
                # Try to extract match num from name
                m = re.match(r'(周[一二三四五六日]\d+)', match_name)
                if m:
                    page_lookup[m.group(1)] = {'id': p['id'], 'name': match_name}
        
        # Get feedback data for this date
        feedback_date = feedback_all.get('dates', {}).get(date_str, {})
        if not feedback_date:
            feedback_date = feedback_all.get(date_str, {})
        
        if isinstance(feedback_date, dict):
            matches = feedback_date.get('feedback', feedback_date.get('matches', []))
        else:
            matches = feedback_date if isinstance(feedback_date, list) else []
        
        # Get results
        results = results_files.get(date_str, {})
        
        # Update each match
        updated = 0
        not_found = 0
        
        for item in matches:
            match_num = item.get('match_num', '')
            predicted = item.get('predicted', '')
            actual_score = item.get('score', '')
            actual_result = item.get('actual', '')
            is_correct = item.get('correct', False)
            rq_pred = item.get('rq_pred', '')
            rq_correct = item.get('rq_correct', False)
            
            # Find page - match_num in feedback is '001', Notion has '周日001' etc
            page_info = page_lookup.get(match_num)
            if not page_info:
                # Try with day prefix (e.g. '001' -> '周日001')
                for k, v in page_lookup.items():
                    if k.endswith(match_num):
                        page_info = v
                        break
            
            if not page_info:
                not_found += 1
                log('WARN', '{}: Notion中未找到'.format(match_num))
                continue
            
            # Update page
            body = {
                'properties': {
                    '实际比分': {'rich_text': [{'text': {'content': actual_score}}]},
                    '实际结果': {'rich_text': [{'text': {'content': actual_result}}]},
                    '预测正确': {'checkbox': is_correct},
                    '让球预测正确': {'checkbox': rq_correct},
                    '反馈日期': {'date': {'start': datetime.now().strftime('%Y-%m-%d')}},
                    '反馈总结': {'rich_text': [{'text': {'content': '竞彩:{} {} | 让球:{} {} | 实际:{} -> 竞彩{} 让球{}'.format(predicted, '✅' if is_correct else '❌', rq_pred, '✅' if rq_correct else '❌', actual_result, '✅' if is_correct else '❌', '✅' if rq_correct else '❌')}}]},
                }
            }
            
            r = notion_patch('https://api.notion.com/v1/pages/' + page_info['id'],
                             json=body)
            if r.status_code == 200:
                updated += 1
                log('OK', '{}: {} {} -> {} ({})'.format(
                    match_num, predicted, actual_result, '✅' if is_correct else '❌', actual_score))
            else:
                log('ERR', '{}: 更新失败 {}'.format(match_num, r.text[:100]))
        
        log('OK', '{}: 更新{}场, 未找到{}场'.format(date_str, updated, not_found))
        total_updated += updated
        total_not_found += not_found
    
    log('DONE', '全部完成: 更新{}场, 未找到{}场'.format(total_updated, total_not_found))

if __name__ == '__main__':
    main()
