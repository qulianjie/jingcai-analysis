const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// 创建三个新字段
const body = JSON.stringify({
    properties: {
        '竞彩欧赔胜': { number: {} },
        '竞彩欧赔平': { number: {} },
        '竞彩欧赔负': { number: {} }
    }
});

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + DB_ID,
    method: 'PATCH',
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
            const newProps = j.properties || {};
            ['竞彩欧赔胜', '竞彩欧赔平', '竞彩欧赔负'].forEach(name => {
                if (newProps[name]) {
                    console.log(`✅ ${name} (${newProps[name].type})`);
                } else {
                    console.log(`❌ ${name} 创建失败`);
                }
            });
        } catch(e) {
            console.log('响应:', d.substring(0, 500));
        }
    });
});
req.on('error', e => console.error(e));
req.write(body);
req.end();
