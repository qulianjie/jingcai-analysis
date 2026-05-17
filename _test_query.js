const https = require('https');
const API_KEY = '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';

// 尝试不带filter的空查询
const body = JSON.stringify({ page_size: 5 });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad717ba80fba45ccb6471eaf4d9/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        try {
            const j = JSON.parse(d);
            if (j.results) {
                console.log('Results:', j.results.length);
                if (j.results.length > 0) {
                    console.log('First result properties:', JSON.stringify(j.results[0].properties, null, 2).substring(0, 800));
                }
            } else {
                console.log('Response:', d);
            }
        } catch(e) {
            console.log('Raw:', d.substring(0, 500));
        }
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(body);
req.end();
