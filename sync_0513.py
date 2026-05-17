# -*- coding: utf-8 -*-
"""快速同步05-13到Notion"""
import requests, json, os, re

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

def notion_request(method, path, data=None):
    url = f'https://api.notion.com{path}'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
    }
    resp = requests.request(method, url, json=data, headers=headers, timeout=30)
    return resp.status_code, resp.json() if resp.text else {}

# 读取比赛列表
match_data_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-13\matches_data.json'
with open(match_data_path, encoding='utf-8') as f:
    match_data = json.load(f)

all_matches = []
for day, info in match_data['groups'].items():
    all_matches.extend(info['matches'])

print(f'共 {len(all_matches)} 场比赛')

report_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-13'

def extract_from_report(content, label):
    if label == '澳门亚盘':
        conclusion_section = re.search(r'# [\u4e5d9][\u90e8\u9879\u5206\u7ae0][\s\S]*?(?=# [^\u4e5d9]|$)', content)
        if conclusion_section:
            m = re.search(r'\|\s*澳门亚盘\s*\|\s*([^|]+)\|\s*([^|]+)\|', conclusion_section.group())
            if m:
                return m[1].strip() + ' | ' + m[2].strip()
        for m in re.finditer(r'\|\s*澳门亚盘\s*\|\s*([^|]+)\|\s*([^|]+)\|', content):
            val = m[1].strip()
            if '利好' in val or '中立' in val:
                return val + ' | ' + m[2].strip()
        return ''
    m = re.search(r'\|\s*' + re.escape(label) + r'\s*\|\s*([^|]+)\|\s*([^|]+)\|', content)
    if m:
        return m[1].strip() + ' | ' + m[2].strip()
    return ''

count = 0
for match in all_matches:
    matchnum = match.get('matchnum', '')
    home = match.get('home', '')
    away = match.get('away', '')
    league = match.get('league', '')
    fid = match.get('fid', '')
    rq = match.get('rq', '')
    
    # 查找对应报告
    report_file = None
    for f in os.listdir(report_dir):
        if f.endswith('.md') and matchnum[:2] in f and matchnum[2:] in f:
            report_file = os.path.join(report_dir, f)
            break
    
    if not report_file:
        print(f'  [SKIP] 未找到报告: {matchnum}')
        continue
    
    with open(report_file, encoding='utf-8') as f:
        content = f.read()
    
    pred_match = re.search(r'【竞彩预测】\s*([^\n]+)', content)
    conf_match = re.search(r'【竞彩信心】\s*(\d+)', content)
    prediction = pred_match.group(1).strip() if pred_match else ''
    confidence = int(conf_match.group(1)) if conf_match else 0
    
    trend_panlu = extract_from_report(content, '盘路匹配')
    trend_europe = extract_from_report(content, '欧赔趋势')
    trend_handicap = extract_from_report(content, '让球同赔')
    trend_macau = extract_from_report(content, '澳门亚盘')
    trend_baijia = extract_from_report(content, '百家对比')
    
    # 查询Notion中是否已有
    status, data = notion_request('POST', f'/v1/databases/{DB_ID}/query', {
        'filter': {'property': '竞彩编号', 'title': {'contains': matchnum}},
        'page_size': 10,
    })
    
    existing_page = None
    if data.get('results'):
        existing_page = data['results'][0]
    
    props = {
        'Name': {'title': [{'text': {'content': f'{matchnum} {home}vs{away}'}}]},
        '竞彩编号': {'title': [{'text': {'content': matchnum}}]},
        '比赛日期': {'date': {'start': '2026-05-13'}},
        '联赛': {'rich_text': [{'text': {'content': league}}]},
        '主队': {'rich_text': [{'text': {'content': home}}]},
        '客队': {'rich_text': [{'text': {'content': away}}]},
        '竞彩预测': {'rich_text': [{'text': {'content': prediction}}]},
        '竞彩信心': {'number': confidence},
        '最终报告': {'url': {'url': f'file:///{report_file.replace(chr(92), "/")}'}},
        '盘路匹配': {'rich_text': [{'text': {'content': trend_panlu}}]},
        '欧赔趋势': {'rich_text': [{'text': {'content': trend_europe}}]},
        '让球趋势': {'rich_text': [{'text': {'content': trend_handicap}}]},
        '澳门亚盘': {'rich_text': [{'text': {'content': trend_macau}}]},
        '百家对比': {'rich_text': [{'text': {'content': trend_baijia}}]},
    }
    
    if existing_page:
        status, data = notion_request('PATCH', f'/v1/pages/{existing_page["id"]}', {'properties': props})
    else:
        props['数据库'] = {'rich_text': [{'text': {'content': fid}}]}
        status, data = notion_request('POST', '/v1/pages', {'parent': {'database_id': DB_ID}, 'properties': props})
    
    if status in [200, 201]:
        print(f'  [OK] {matchnum} {home}vs{away} (信心{confidence}%)')
        count += 1
    else:
        print(f'  [ERR] {matchnum} status={status} {json.dumps(data, ensure_ascii=False)[:200]}')

print(f'\n完成: 同步 {count}/{len(all_matches)} 场')
