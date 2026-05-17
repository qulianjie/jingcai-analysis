// 查询技术学习日报数据库内容
const https = require('https');
const API_KEY = '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';
const DB_ID = 'dc3cfd289c6c49dd93d28fb2534f5284';

const data = JSON.stringify({ 
    page_size: 100,
    sorts: [{ property: '名称', direction: 'ascending' }]
});

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}/query`,
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Response:', d.substring(0, 2000));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
