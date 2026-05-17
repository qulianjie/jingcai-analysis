const https = require('https');
const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

const body = JSON.stringify({ page_size: 100 });
const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + DB_ID + '/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2025-09-03',
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
            if (j.results) {
                console.log('结果数:', j.results.length);
                console.log('has_more:', j.has_more);
                if (j.results.length > 0) {
                    console.log('字段:', Object.keys(j.results[0].properties).join(', '));
                    console.log('第一条:', JSON.stringify(j.results[0].properties, null, 2).substring(0, 500));
                }
            } else {
                console.log('响应:', d.substring(0, 500));
            }
        } catch(e) {
            console.log('原始响应:', d.substring(0, 500));
        }
    });
});
req.on('error', e => console.error(e));
req.write(body);
req.end();
