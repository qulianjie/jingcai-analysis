// 检查数据库列
const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}`,
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        const props = Object.keys(r.properties || {});
        console.log('列数:', props.length);
        console.log('列名:', props.join(', '));
        console.log('有让球预测:', props.includes('让球预测'));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.end();
