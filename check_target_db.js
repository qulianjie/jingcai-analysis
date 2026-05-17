const https = require('https');

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad7-17ba-802f-acb7-ebfd74db132c',
    method: 'GET',
    headers: {
        'Authorization': 'Bearer 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',
        'Notion-Version': '2022-06-28'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        console.log('Title:', r.title);
        console.log('Object:', r.object);
        console.log('\nFields:');
        for (const [k, v] of Object.entries(r.properties)) {
            console.log(`  ${k}: ${v.type}`);
        }
    });
});
req.end();
