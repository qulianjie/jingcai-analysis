# -*- coding: utf-8 -*-
"""删除Notion中5月8日周六周日的比赛"""
import json, os, subprocess

# Read Notion API key
with open(os.path.expanduser('~/.config/notion/api_key'), 'r') as f:
    api_key = f.read().strip()

db_id = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

# Query for 2026-05-08 entries
payload = {
    "filter": {
        "and": [
            {"property": "比赛日期", "date": {"equals": "2026-05-08"}}
        ]
    },
    "page_size": 100
}

# Use node to query (avoid PowerShell encoding issues)
node_script = '''
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

import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
    f.write(node_script)
    script_path = f.name

result = subprocess.run(
    ['node', script_path, api_key, db_id, json.dumps(payload)],
    capture_output=True, text=True, timeout=30
)
os.unlink(script_path)

lines = result.stdout.strip().split('\n')
print(lines[0])  # Total

to_delete = []
for line in lines[1:]:
    parts = line.split('|')
    if len(parts) == 5:
        id, num, date, home, away = parts
        # Check if match_num contains 周六 or 周日
        if '周六' in num or '周日' in num:
            to_delete.append((id, num, home, away))
            print('DELETE: %s %s %s vs %s' % (num, date, home, away))

print('\nTotal to delete: %d' % len(to_delete))

if not to_delete:
    print('No entries match criteria (周六/周日 on 2026-05-08)')
    # Check what's actually there
    print('\nAll 2026-05-08 entries:')
    for line in lines[1:]:
        parts = line.split('|')
        if len(parts) == 5:
            print('  %s | %s | %s vs %s' % (parts[1], parts[2], parts[3], parts[4]))
