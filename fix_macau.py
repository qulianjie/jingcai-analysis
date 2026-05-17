# -*- coding: utf-8 -*-
"""修复05-12的澳门亚盘列：从本地报告提取趋势格式，更新到Notion"""
import os, re, json, http.client
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

NOTION_API_KEY = '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'
DATABASE_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'
TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks')

def notion_request(method, endpoint, data=None):
    conn = http.client.HTTPSConnection('api.notion.com')
    headers = {
        'Authorization': f'Bearer {NOTION_API_KEY}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }
    body = json.dumps(data).encode('utf-8') if data else None
    conn.request(method, endpoint, body, headers)
    res = conn.getresponse()
    d = res.read().decode('utf-8')
    try:
        return {'status': res.status, 'data': json.loads(d)}
    except:
        return {'status': res.status, 'data': d}

def query_by_date(date_str):
    data = {
        'filter': {'property': '比赛日期', 'date': {'equals': date_str}},
        'page_size': 100,
    }
    res = notion_request('POST', f'/v1/databases/{DATABASE_ID}/query', data)
    return res.get('data', {}).get('results', [])

def update_macau(page_id, macau_trend):
    props = {
        '澳门亚盘': {'rich_text': [{'text': {'content': macau_trend}}]}
    }
    res = notion_request('PATCH', f'/v1/pages/{page_id}', {'properties': props})
    return res['status'] == 200

def main():
    date_str = '2026-05-12'
    task_dir = os.path.join(TASKS_DIR, date_str)
    
    # 查询Notion记录
    notion_records = query_by_date(date_str)
    print(f'Notion记录数: {len(notion_records)}')
    
    # 读取本地报告，提取澳门亚盘趋势
    files = [f for f in os.listdir(task_dir) if f.endswith('.md') and 'sunday' not in f.lower()]
    
    # 建立编号到澳门亚盘趋势的映射
    macau_map = {}
    for f in files:
        path = os.path.join(task_dir, f)
        content = open(path, 'r', encoding='utf-8').read()
        
        # 提取编号
        num_match = re.search(r'周[一二三四五六日](\d{3})', f)
        if not num_match:
            continue
        num = num_match.group(1)
        
        # 提取澳门亚盘趋势: | 澳门亚盘 | +0.061 利好主 | 12% |
        trend_match = re.search(r'\|\s*澳门亚盘\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|', content)
        if trend_match:
            value = trend_match.group(1).strip()  # +0.061 利好主
            pct = trend_match.group(2).strip()    # 12%
            macau_map[num] = f'{value} | {pct}'
        else:
            # Fallback: try to find just the trend line
            trend_match2 = re.search(r'(澳门亚盘:\s*[^\n]+)', content)
            if trend_match2:
                text = trend_match2.group(1).strip()
                # Extract the value and direction
                val_match = re.search(r'([+-][\d.]+)\s*(利好[主客])', text)
                if val_match:
                    value = val_match.group(1) + ' ' + val_match.group(2)
                    pct_match = re.search(r'（分值[\d.-]+\s*[\d.]+%）', text)
                    pct = pct_match.group(0) if pct_match else ''
                    macau_map[num] = f'{value} | {pct}' if pct else value
    
    print(f'提取到 {len(macau_map)} 条澳门亚盘数据')
    
    # 更新Notion
    total_updated = 0
    for record in notion_records:
        page_id = record['id']
        notion_name = record.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', '')
        num_match = re.search(r'(\d{3})', notion_name)
        num = num_match.group(1) if num_match else ''
        
        if num in macau_map:
            trend = macau_map[num]
            success = update_macau(page_id, trend)
            if success:
                print(f'  [OK] {notion_name}: {trend}')
                total_updated += 1
            else:
                print(f'  [FAIL] {notion_name}')
    
    print(f'\n完成: 更新 {total_updated}/{len(notion_records)} 条')

if __name__ == '__main__':
    main()
