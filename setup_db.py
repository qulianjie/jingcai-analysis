# Add properties to the new jingcai database using Python requests
import requests
import json

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

headers = {
    'Authorization': 'Bearer ' + API_KEY,
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json'
}

# First get current database info
resp = requests.get(f'https://api.notion.com/v1/databases/{DB_ID}', headers=headers)
print('GET status:', resp.status_code)
db = resp.json()
print('Title:', db.get('title', [{}])[0].get('plain_text', ''))
print('Properties:', json.dumps(db.get('properties', {}), indent=2, ensure_ascii=False)[:500])

# Now PATCH with new properties
properties = {
    '竞彩编号': { 'rich_text': {} },
    '比赛日期': { 'date': {} },
    '联赛': { 'rich_text': {} },
    '主队': { 'rich_text': {} },
    '客队': { 'rich_text': {} },
    '竞彩预测': { 'rich_text': {} },
    '竞彩信心': { 'select': { 'options': [
        { 'name': '高' }, { 'name': '中' }, { 'name': '低' }
    ]}},
    '最终报告': { 'rich_text': {} },
    '盘路匹配': { 'rich_text': {} },
    '欧赔趋势': { 'rich_text': {} },
    '让球趋势': { 'rich_text': {} },
    '亚盘趋势': { 'rich_text': {} },
    '百家对比': { 'rich_text': {} },
    '实际比分': { 'rich_text': {} },
    '实际结果': { 'select': { 'options': [
        { 'name': '主胜' }, { 'name': '平局' }, { 'name': '客胜' }
    ]}},
    '预测正确': { 'checkbox': {} },
    '反馈日期': { 'date': {} },
    '反馈总结': { 'rich_text': {} },
    '备注': { 'rich_text': {} }
}

body = { 'properties': properties }
resp2 = requests.patch(
    f'https://api.notion.com/v1/databases/{DB_ID}',
    headers=headers,
    json=body
)
print('\nPATCH status:', resp2.status_code)
print('Response:', resp2.text[:1000])

# Verify
if resp2.status_code == 200:
    result = resp2.json()
    props = result.get('properties', {})
    print('\nField count:', len(props))
    for k in props:
        print('  -', k)
