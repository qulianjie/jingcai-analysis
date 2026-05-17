const https = require('https');

const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

// 先删除旧的5月10日记录
// 查询所有记录
const data = JSON.stringify({ page_size: 100 });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad7-17ba-80fb-a45c-cb6471eaf4d9/query',
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
        const r = JSON.parse(d);
        // 删除所有5月10日的记录
        const toDelete = r.results.filter(p => p.properties['日期']?.title?.[0]?.plain_text === '2026-05-10');
        console.log('Found', toDelete.length, 'records to delete');
        
        let deleted = 0;
        for (const page of toDelete) {
            const delData = JSON.stringify({ archived: true });
            const delReq = https.request({
                hostname: 'api.notion.com',
                path: `/v1/pages/${page.id}`,
                method: 'PATCH',
                headers: {
                    'Authorization': 'Bearer ' + API_KEY,
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(delData)
                }
            }, delRes => {
                let dd = '';
                delRes.on('data', c => dd += c);
                delRes.on('end', () => {
                    deleted++;
                    if (deleted === toDelete.length) {
                        console.log('Deleted', deleted, 'records');
                        // 现在添加新字段
                        addFields();
                    }
                });
            });
            delReq.write(delData);
            delReq.end();
        }
    });
});
req.write(data);
req.end();

function addFields() {
    const props = {
        '竞彩': { select: {} },
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
}

function insertData() {
    const fs = require('fs');
    const logData = JSON.parse(fs.readFileSync('C:/Users/lianjie/.openclaw/workspace/data/jingcai/feedback_2026-05-10.json', 'utf8'));
    const groups = logData.groups;
    const sortedGroups = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);
    
    let inserted = 0;
    for (const [key, stats] of sortedGroups) {
        const [pred, zj, rq] = key.split('|');
        
        const data = JSON.stringify({
            parent: { database_id: DB_ID },
            properties: {
                '日期': { title: [{ text: { content: '2026-05-10' } }] },
                '竞彩': { select: { name: pred } },
                '庄家': { select: { name: zj } },
                '让球': { select: { name: rq } },
                '场数': { number: stats.total },
                '胜': { number: stats.胜 },
                '平': { number: stats.平 },
                '负': { number: stats.负 }
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
                if (inserted === sortedGroups.length) {
                    console.log('✅ Inserted', inserted, 'rows');
                }
            });
        });
        req.write(data);
        req.end();
    }
}
