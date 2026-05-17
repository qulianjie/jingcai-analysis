const https = require('https');

const API_KEY = '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';

// 查询所有5月10日记录
const data = JSON.stringify({ page_size: 100 });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad7-17ba-80fb-a45c-cb6471eaf4d9/query',
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
        const may10 = r.results.filter(p => p.properties['日期']?.title?.[0]?.plain_text === '2026-05-10');
        console.log('Found', may10.length, 'records for 2026-05-10');
        
        let deleted = 0;
        for (const page of may10) {
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
                    if (deleted === may10.length) {
                        console.log('Archived', deleted, 'records');
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
