const https = require('https');
const API_KEY = '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';

// 尝试用页面方式访问
const ids = [
    '35d91ad717ba80fba45ccb6471eaf4d9',
    '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9',
];

for (const id of ids) {
    // 尝试作为页面访问
    const req = https.request({
        hostname: 'api.notion.com',
        path: '/v1/pages/' + id,
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + API_KEY,
            'Notion-Version': '2025-09-03',
        }
    }, res => {
        let d = '';
        res.on('data', c => d += c);
        res.on('end', () => {
            console.log('Page ' + id + ' -> ' + res.statusCode + ': ' + d.substring(0, 300));
        });
    });
    req.on('error', e => console.log('Page ' + id + ' -> ' + e.message));
    req.end();
}
