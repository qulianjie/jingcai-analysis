// 检查数据库属性
const https = require('https');
const API_KEY = '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';
const DB_ID = 'a5e71b20-9c11-4b56-aeb5-134fef482fe3';

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}`,
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2025-09-03'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        console.log('Title:', r.title?.[0]?.plain_text);
        console.log('Props count:', Object.keys(r.properties || {}).length);
        console.log('Props:', Object.keys(r.properties || {}).join(', '));
    });
});
req.end();
