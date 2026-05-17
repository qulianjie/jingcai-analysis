const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const data = JSON.stringify({
    filter: { property: '比赛日期', date: { equals: '2026-05-07' } },
    page_size: 100
});

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + DB_ID + '/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        try {
            const r = JSON.parse(body);
            if (!r.results) { console.log('Error:', JSON.stringify(r)); return; }
            r.results.forEach(p => {
                const t = p.properties.Name?.title?.[0]?.plain_text || '';
                const pr = p.properties['竞彩预测']?.rich_text?.[0]?.plain_text || '';
                const sc = p.properties['实际比分']?.rich_text?.[0]?.plain_text || '';
                console.log(t + '|' + pr + '|' + sc);
            });
        } catch (e) { console.log('Parse error:', e.message); }
    });
});
req.write(data);
req.end();
