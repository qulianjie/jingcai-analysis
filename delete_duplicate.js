const https = require('https');

const pageId = '35d91ad7-17ba-81db-ba09-cae7a5f717f0';

const data = JSON.stringify({ archived: true });

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/pages/${pageId}`,
    method: 'PATCH',
    headers: {
        'Authorization': 'Bearer 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',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        console.log('Archived:', r.archived);
    });
});
req.write(data);
req.end();
