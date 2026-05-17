# -*- coding: utf-8 -*-
"""
批量反馈Notion同步
用法: python batch_notion_feedback.py 2026-05-02 2026-05-03 2026-05-04
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

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def get_db_fields():
    """获取数据库字段映射"""
    r = requests.get('https://api.notion.com/v1/databases/' + DATABASE_ID, headers=H, timeout=15)
    db = r.json()
    props = db.get('properties', {})
    fields = {}
    for name, prop in props.items():
        fields[name] = prop.get('type', '?')
    return fields

def find_page_by_date_and_num(date_str, match_num):
    """按日期和竞彩编号查找Notion页面"""
    body = {
        'page_size': 100,
        'filter': {
            'and': [
                {'property': '比赛日期', 'date': {'equals': date_str}},
            ]
        }
    }
    r = requests.post('https://api.notion.com/v1/databases/' + DATABASE_ID + '/query', headers=H, json=body, timeout=30)
    result = r.json()
    
    for p in result.get('results', []):
        props = p.get('properties', {})
        # Check if this match matches
        name = ''
        for pname, pval in props.items():
            if pval.get('type') == 'title':
                name = pval.get('title', [{}])[0].get('plain_text', '') if pval.get('title') else ''
                break
        
        if match_num in name:
            return p['id'], props
    
    return None, None

def update_notion_page(page_id, fields_data):
    """更新Notion页面"""
    body = {'properties': {}}
    
    for field_name, field_value in fields_data.items():
        if field_value is None:
            continue
        
        # Find the property
        for pname in ['实际比分', '实际结果', '预测正确', '反馈日期', '反馈总结']:
            if pname in field_name or field_name in pname:
                if field_name == '实际比分':
                    body['properties'][pname] = {'rich_text': [{'text': {'content': str(field_value)}}]}
                elif field_name == '实际结果':
                    body['properties'][pname] = {'rich_text': [{'text': {'content': str(field_value)}}]}
                elif field_name == '预测正确':
                    body['properties'][pname] = {'checkbox': bool(field_value)}
                elif field_name == '反馈日期':
                    body['properties'][pname] = {'date': {'start': str(field_value)}}
                elif field_name == '反馈总结':
                    body['properties'][pname] = {'rich_text': [{'text': {'content': str(field_value)}}]}
    
    if body['properties']:
        r = requests.patch('https://api.notion.com/v1/pages/' + page_id, headers=H, json=body, timeout=30)
        return r.status_code == 200
    return False

def main():
    if len(sys.argv) < 2:
        print('用法: python batch_notion_feedback.py <date1> [date2] ...')
        sys.exit(1)
    
    log('START', '批量反馈Notion同步')
    
    dates = sys.argv[1:]
    
    # Load feedback data
    feedback_file = os.path.join(SCRIPT_DIR, 'learnings/feedback.json')
    if not os.path.exists(feedback_file):
        log('ERR', '反馈文件不存在: {}'.format(feedback_file))
        sys.exit(1)
    
    with open(feedback_file, 'r', encoding='utf-8') as f:
        feedback_data = json.load(f)
    
    # Get Notion fields
    db_fields = get_db_fields()
    log('INFO', 'Notion字段: {}'.format(', '.join(sorted(db_fields.keys()))))
    
    total_updated = 0
    total_found = 0
    
    for date_str in dates:
        log('DATE', '处理 {}'.format(date_str))
        
        # Find feedback data for this date
        date_feedback = feedback_data.get('dates', {}).get(date_str, {})
        if not date_feedback:
            # Try direct key
            date_feedback = feedback_data.get(date_str, {})
        
        if not date_feedback:
            log('WARN', '未找到 {} 的反馈数据'.format(date_str))
            continue
        
        if isinstance(date_feedback, list):
            # Convert to dict by match_num
            items = date_feedback
        elif isinstance(date_feedback, dict):
            items = date_feedback.get('matches', []) if 'matches' in date_feedback else [date_feedback]
        else:
            log('WARN', '未知格式: {}'.format(type(date_feedback)))
            continue
        
        updated = 0
        found = 0
        
        for item in items:
            match_num = item.get('match_num', item.get('matchnum', ''))
            actual_score = item.get('actual_score', item.get('score', ''))
            actual_result = item.get('actual_result', item.get('result', ''))
            predicted = item.get('predicted', item.get('prediction', ''))
            is_correct = item.get('is_correct', item.get('correct', False))
            
            # Find page in Notion
            page_id, props = find_page_by_date_and_num(date_str, match_num)
            if page_id:
                found += 1
                # Update
                fields = {
                    '实际比分': actual_score,
                    '实际结果': actual_result,
                    '预测正确': is_correct,
                    '反馈日期': datetime.now().strftime('%Y-%m-%d'),
                    '反馈总结': '预测:{} 实际:{} -> {}'.format(predicted, actual_result, '✅正确' if is_correct else '❌错误'),
                }
                if update_notion_page(page_id, fields):
                    updated += 1
                    log('OK', '{}: 已更新'.format(match_num))
                else:
                    log('ERR', '{}: 更新失败'.format(match_num))
            else:
                log('WARN', '{}: Notion中未找到'.format(match_num))
        
        log('OK', '{}: 找到{}场, 更新{}场'.format(date_str, found, updated))
        total_updated += updated
        total_found += found
    
    log('DONE', '全部完成: 找到{}场, 更新{}场'.format(total_found, total_updated))

if __name__ == '__main__':
    main()
