// 通过search API找到技术学习日报数据库的内容
const https = require('https');
const API_KEY = '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';

const data = JSON.stringify({
    query: '技术学习',
    filter: { property: 'object', value: 'database' },
    page_size: 10
});

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/search',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        console.log('Results:', r.results?.length || 0);
        (r.results || []).forEach((item, i) => {
            console.log(`\n[${i+1}] ${item.object}: ${item.id}`);
            console.log(`  Title: ${item.title?.[0]?.plain_text || item.Name?.title?.[0]?.plain_text || 'N/A'}`);
        });
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
