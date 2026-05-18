// 检查data_source的属性
const https = require('https');
const API_KEY = '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';
const DB_ID = 'adfc426c-4777-4ca8-a86d-2fca7dc424f6';

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
        console.log('is_inline:', r.is_inline);
        console.log('data_sources:', JSON.stringify(r.data_sources));
        console.log('properties:', JSON.stringify(r.properties, null, 2));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.end();
