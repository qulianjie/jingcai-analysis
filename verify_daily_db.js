const https = require('https');

const data = JSON.stringify({ page_size: 20 });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad7-17ba-80fb-a45c-cb6471eaf4d9/query',
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
        console.log('Records:', r.results.length);
        r.results.forEach(p => {
            const props = p.properties;
            console.log(
                props['日期']?.title?.[0]?.plain_text, '|',
                props['竞彩']?.select?.name, '|',
                props['庄家']?.select?.name, '|',
                props['让球']?.select?.name, '|',
                props['场数']?.number, '|',
                props['胜']?.number, '|',
                props['平']?.number, '|',
                props['负']?.number
            );
        });
    });
});
req.write(data);
req.end();
