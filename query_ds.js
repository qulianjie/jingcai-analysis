// 用data_source API查询技术学习日报
const https = require('https');
const API_KEY = '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';
const DS_ID = 'fde398b9-17f3-4ede-b55a-29c711f42be1';

const data = JSON.stringify({
    page_size: 100
});

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/data_sources/${DS_ID}/query`,
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
        console.log('Body:', d.substring(0, 3000));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
