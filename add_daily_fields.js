const https = require('https');

const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

// 添加字段到数据库
const props = {
    '总场数': { number: {} },
    '胜': { number: {} },
    '平': { number: {} },
    '负': { number: {} },
    '竞彩正确率': { rich_text: {} },
    '最大分组': { rich_text: {} },
    '最大分组详情': { rich_text: {} },
    '分组明细': { rich_text: {} }
};

const data = JSON.stringify({ properties: props });

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
        try {
            const r = JSON.parse(d);
            console.log('✅ 字段已添加');
            console.log('Fields:', Object.keys(r.properties).join(', '));
        } catch (e) {
            console.log('Error:', d);
        }
    });
});
req.on('error', e => console.log('Error:', e.message));
req.write(data);
req.end();
