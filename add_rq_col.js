// 添加"让球预测"列到数据库
const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const data = JSON.stringify({
    properties: {
        "让球预测": { "rich_text": {} }
    }
});

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}`,
    method: 'PATCH',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        const r = JSON.parse(d);
        const props = Object.keys(r.properties || {});
        console.log('列数:', props.length);
        console.log('有让球预测:', props.includes('让球预测'));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
