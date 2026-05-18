// Check new database properties
const https = require('https');
const key = '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';
const dbId = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + dbId,
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + key,
        'Notion-Version': '2025-09-03'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        if (r.properties) {
            Object.entries(r.properties).forEach(([k, v]) => {
                console.log('  ' + k + ' (' + v.type + ')');
            });
        } else {
            console.log(JSON.stringify(r));
        }
    });
});
req.end();
