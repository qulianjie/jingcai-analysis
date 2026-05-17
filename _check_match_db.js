const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// 查一条数据看当前字段结构
const body = JSON.stringify({ page_size: 1 });
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
        try {
            const j = JSON.parse(d);
            if (j.results && j.results.length > 0) {
                console.log('字段:', Object.keys(j.results[0].properties).join(', '));
            }
        } catch(e) {
            console.log('响应:', d.substring(0, 500));
        }
    });
});
req.on('error', e => console.error(e));
req.write(body);
req.end();
