const https = require('https');
const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

// 简单查询
const body = JSON.stringify({
    page_size: 5,
    filter: {
        property: '日期',
        date: {}
    }
});

console.log('DB ID:', DB_ID);
console.log('Body:', body);

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + DB_ID + '/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Response:', d.substring(0, 500));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(body);
req.end();
