// 用data_source方式查询技术学习日报
const https = require('https');
const API_KEY = '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';
const DB_ID = 'dc3cfd289c6c49dd93d28fb2534f5284';

// 先获取数据库详情
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
        console.log('Status:', res.statusCode);
        console.log('Title:', r.title?.[0]?.plain_text);
        console.log('is_inline:', r.is_inline);
        console.log('data_sources:', JSON.stringify(r.data_sources));
        console.log('properties:', JSON.stringify(r.properties));
        console.log('Full response:', JSON.stringify(r, null, 2));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.end();
