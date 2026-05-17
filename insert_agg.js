const https = require('https');

const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-802f-acb7-ebfd74db132c';

// 添加字段
const props = {
    '庄家': { select: {} },
    '让球': { select: {} },
    '场数': { number: {} },
    '胜': { number: {} },
    '平': { number: {} },
    '负': { number: {} }
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
        console.log('✅ Fields added');
        insertData();
    });
});
req.write(data);
req.end();

function insertData() {
    const fs = require('fs');
    const agg = JSON.parse(fs.readFileSync('C:/Users/lianjie/.openclaw/workspace/data/jingcai/daily_agg.json', 'utf8'));
    
    let inserted = 0;
    const total = Object.keys(agg).length;
    
    for (const [key, stats] of Object.entries(agg)) {
        const [jp, zj, rq] = key.split('|');
        
        const data = JSON.stringify({
            parent: { database_id: DB_ID },
            properties: {
                '竞彩': { title: [{ text: { content: jp } }] },
                '庄家': { select: { name: zj } },
                '让球': { select: { name: rq } },
                '场数': { number: stats.total },
                '胜': { number: stats.wins },
                '平': { number: stats.draws },
                '负': { number: stats.losses }
            }
        });
        
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages',
            method: 'POST',
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
                inserted++;
                if (inserted === total) {
                    console.log('✅ Inserted', inserted, 'rows');
                }
            });
        });
        req.write(data);
        req.end();
    }
}
