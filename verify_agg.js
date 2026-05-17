const https = require('https');

const data = JSON.stringify({ page_size: 20 });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad7-17ba-802f-acb7-ebfd74db132c/query',
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
        console.log('历史汇总记录:', r.results.length);
        for (const p of r.results) {
            const pr = p.properties;
            console.log(
                pr['竞彩']?.title?.[0]?.plain_text, '|',
                pr['庄家']?.select?.name, '|',
                pr['让球']?.select?.name, '|',
                pr['场数']?.number, '|',
                pr['胜']?.number, '|',
                pr['平']?.number, '|',
                pr['负']?.number
            );
        }
    });
});
req.write(data);
req.end();
