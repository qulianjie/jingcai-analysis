// 通过搜索API找到技术学习日报数据库
const https = require('https');
const API_KEY = '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';

// 搜索所有database
const data = JSON.stringify({
    filter: { property: 'object', value: 'database' },
    page_size: 50
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
        console.log('Total:', r.results?.length || 0);
        (r.results || []).forEach((item, i) => {
            console.log(`\n[${i+1}] ${item.title?.[0]?.plain_text || 'N/A'}`);
            console.log(`  ID: ${item.id}`);
            console.log(`  Parent: ${JSON.stringify(item.parent)}`);
            console.log(`  DataSources: ${JSON.stringify(item.data_sources)}`);
            console.log(`  Props: ${Object.keys(item.properties || {}).join(', ')}`);
        });
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
