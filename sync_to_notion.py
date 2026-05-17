# -*- coding: utf-8 -*-
"""
将5月7日以后的所有最终报告上传到Notion数据库
数据库ID: 36191ad7-17ba-80be-b656-cc7c0baaa33d
"""
import os, sys, json, time, requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Notion API key (UTF-16 encoded)
key_path = os.path.expanduser('~/.config/notion/api_key')
with open(key_path, 'rb') as f:
    NOTION_TOKEN = f.read().decode('utf-16').strip()

DATABASE_ID = '36191ad717ba80beb656cc7c0baaa33d'

def notion_create_page(database_id, title, content_md):
    """创建Notion页面"""
    blocks = markdown_to_blocks(content_md)
    
    url = 'https://api.notion.com/v1/pages'
    headers = {
        'Authorization': 'Bearer %s' % NOTION_TOKEN,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
    }
    
    data = {
        'parent': {'database_id': database_id},
        'properties': {
            'Name': {'title': [{'text': {'content': title}}]},
            '类别': {'select': {'name': 'match'}},
        },
        'children': blocks,
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('id')
        else:
            print('  ERROR: %d %s' % (resp.status_code, resp.text[:200]))
            return None
    except Exception as e:
        print('  ERROR: %s' % str(e))
        return None

def markdown_to_blocks(md_text, max_size=1950):
    """将markdown文本转为Notion blocks"""
    blocks = []
    paragraphs = md_text.split('\n\n')
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        
        if p.startswith('# '):
            blocks.append({
                'object': 'block',
                'type': 'heading_1',
                'heading_1': {
                    'rich_text': [{'type': 'text', 'text': {'content': p[2:].strip()}}]
                }
            })
        elif p.startswith('## '):
            blocks.append({
                'object': 'block',
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{'type': 'text', 'text': {'content': p[3:].strip()}}]
                }
            })
        elif p.startswith('### '):
            blocks.append({
                'object': 'block',
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{'type': 'text', 'text': {'content': p[4:].strip()}}]
                }
            })
        else:
            for i in range(0, len(p), max_size):
                chunk = p[i:i+max_size]
                blocks.append({
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [{'type': 'text', 'text': {'content': chunk}}]
                    }
                })
        
        if len(blocks) >= 90:
            break
    
    if not blocks:
        blocks.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': '(empty)'}}]
            }
        })
    
    return blocks

def find_reports():
    """找出5月7日以后的所有报告"""
    dates = []
    d = datetime(2026, 5, 7)
    today = datetime.now()
    while d <= today:
        dates.append(d.strftime('%Y-%m-%d'))
        d += __import__('datetime').timedelta(days=1)
    
    reports = []
    for date in dates:
        task_dir = os.path.join(BASE_DIR, 'tasks', date)
        if not os.path.isdir(task_dir):
            continue
        for f in sorted(os.listdir(task_dir)):
            if f.endswith('.md') and not f.startswith('final') and f != 'sunday_matches.md':
                reports.append((date, f, os.path.join(task_dir, f)))
    
    return reports

def main():
    print('Finding reports...')
    reports = find_reports()
    print('Found %d reports\n' % len(reports))
    
    success = 0
    failed = 0
    
    for date, name, path in reports:
        print('%s: %s...' % (date, name[:30]), end=' ')
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        page_id = notion_create_page(DATABASE_ID, name, content)
        if page_id:
            print('OK')
            success += 1
        else:
            print('FAIL')
            failed += 1
        
        time.sleep(0.5)
    
    print('\nDone! Success: %d, Failed: %d' % (success, failed))

if __name__ == '__main__':
    main()
