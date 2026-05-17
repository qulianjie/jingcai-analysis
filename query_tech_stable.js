// 直接访问技术学习日报数据库 - 换用稳定版API
const https = require('https');
const API_KEY = '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';
const DB_ID = 'dc3cfd289c6c49dd93d28fb2534f5284';

// 先用GET获取数据库结构
const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}`,
    method: 'GET',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28'  // 使用稳定版
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        const r = JSON.parse(d);
        console.log('Title:', r.title?.[0]?.plain_text);
        console.log('is_inline:', r.is_inline);
        console.log('properties keys:', Object.keys(r.properties || {}));
        console.log('properties:', JSON.stringify(r.properties, null, 2).substring(0, 2000));
    });
});
req.on('error', e => console.error('Error:', e.message));
req.end();
