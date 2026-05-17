const https = require('https');

const API_KEY = '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';
const SOURCE_DB = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';
const TARGET_DB = '35d91ad7-17ba-802f-acb7-ebfd74db132c';

// 1. 查询源数据库所有记录
const data = JSON.stringify({ page_size: 100 });

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${SOURCE_DB}/query`,
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        console.log('源记录:', r.results.length);
        
        // 按 竞彩|庄家|让球 分组汇总
        const agg = {};
        for (const page of r.results) {
            const props = page.properties;
            const jp = props['竞彩']?.select?.name || '未知';
            const zj = props['庄家']?.select?.name || '未知';
            const rq = props['让球']?.select?.name || '未知';
            const count = props['场数']?.number || 0;
            const wins = props['胜']?.number || 0;
            const draws = props['平']?.number || 0;
            const losses = props['负']?.number || 0;
            
            const key = `${jp}|${zj}|${rq}`;
            if (!agg[key]) agg[key] = { total: 0, wins: 0, draws: 0, losses: 0 };
            agg[key].total += count;
            agg[key].wins += wins;
            agg[key].draws += draws;
            agg[key].losses += losses;
        }
        
        console.log('汇总分组:', Object.keys(agg).length);
        
        // 2. 先清空目标数据库
        const data2 = JSON.stringify({ page_size: 100 });
        const req2 = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${TARGET_DB}/query`,
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
        }, res2 => {
            let d2 = '';
            res2.on('data', c => d2 += c);
            res2.on('end', () => {
                const r2 = JSON.parse(d2);
                console.log('目标记录:', r2.results.length);
                
                let archived = 0;
                for (const page of r2.results) {
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
                            archived++;
                            if (archived === r2.results.length) {
                                console.log('已清空目标数据库');
                                insertAgg(agg);
                            }
                        });
                    });
                    delReq.write(delData);
                    delReq.end();
                }
                
                if (r2.results.length === 0) {
                    insertAgg(agg);
                }
            });
        });
        req2.write(data2);
        req2.end();
    });
});
req.write(data);
req.end();

function insertAgg(agg) {
    let inserted = 0;
    const total = Object.keys(agg).length;
    
    for (const [key, stats] of Object.entries(agg)) {
        const [jp, zj, rq] = key.split('|');
        
        const data = JSON.stringify({
            parent: { database_id: TARGET_DB },
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
                    console.log('✅ 已插入', inserted, '条汇总记录');
                }
            });
        });
        req.write(data);
        req.end();
    }
}
