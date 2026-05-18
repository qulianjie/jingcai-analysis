const https = require('https');

const data = JSON.stringify({
    filter: { property: '比赛日期', date: { equals: '2026-05-10' } },
    page_size: 3
});

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer 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',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        r.results.forEach(p => {
            const nm = p.properties.Name?.title?.[0]?.plain_text;
            const jp = p.properties['竞彩预测']?.rich_text?.[0]?.plain_text;
            const zj = p.properties['步26_庄家最看好']?.rich_text?.[0]?.plain_text;
            const rq = p.properties['让球预测']?.rich_text?.[0]?.plain_text;
            console.log(nm, '| 竞彩:', jp, '| 庄家:', zj, '| 让球:', rq);
        });
    });
});
req.write(data);
req.end();
