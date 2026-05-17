const https = require('https');
const API_KEY = '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';

const ids = [
    '35d91ad717ba80fba45ccb6471eaf4d9',
    '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9',
];

for (const id of ids) {
    const body = JSON.stringify({ page_size: 1 });
    const req = https.request({
        hostname: 'api.notion.com',
        path: '/v1/databases/' + id + '/query',
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
            console.log(id + ' -> ' + res.statusCode + ': ' + d.substring(0, 200));
        });
    });
    req.on('error', e => console.log(id + ' -> ' + e.message));
    req.write(body);
    req.end();
}
