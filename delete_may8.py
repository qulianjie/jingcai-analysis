# -*- coding: utf-8 -*-
"""Delete Notion entries for May 8 with 周六/周日 labels"""
import json, os, subprocess

api_key_path = os.path.expanduser('~/.config/notion/api_key')
with open(api_key_path, 'r', encoding='utf-8-sig') as f:
    api_key = f.read().strip()

db_id = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

payload = {
    "filter": {
        "property": "比赛日期",
        "date": {"equals": "2026-05-08"}
    },
    "page_size": 100
}

node_script = r'''
const https = require('https');
const apiKey = process.argv[1];
const dbId = process.argv[2];
const payload = process.argv[3];

const data = JSON.stringify(JSON.parse(payload));
const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + dbId + '/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + apiKey,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        const r = JSON.parse(body);
        console.log('Total: ' + r.results.length);
        r.results.forEach(row => {
            const id = row.id;
            const num = row.properties['竞彩编号']?.title?.[0]?.plain_text || '';
            const date = row.properties['比赛日期']?.date?.start || '';
            const home = row.properties['主队']?.rich_text?.[0]?.plain_text || '';
            const away = row.properties['客队']?.rich_text?.[0]?.plain_text || '';
            console.log(id + '|' + num + '|' + date + '|' + home + '|' + away);
        });
    });
});
req.write(data);
req.end();
'''

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\temp_query.js', 'w', encoding='utf-8') as f:
    f.write(node_script)

result = subprocess.run(
    ['node', r'C:\Users\lianjie\.openclaw\workspace\jingcai\temp_query.js', api_key, db_id, json.dumps(payload)],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
if result.stderr:
    print('STDERR:', result.stderr[:500])
