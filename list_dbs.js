const https = require('https');

const API_KEY = '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';
const PARENT_ID = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71';

// Search for all databases under the 竞彩 parent page
const data = JSON.stringify({
    filter: {
        property: 'parent',
        page_id: { equals: PARENT_ID }
    },
    page_size: 100
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
        const results = r.results || [];
        console.log(`Found ${results.length} items under 竞彩 parent\n`);
        
        results.forEach(item => {
            if (item.object === 'database') {
                const title = item.title?.[0]?.plain_text || '(untitled)';
                const props = item.properties ? Object.keys(item.properties) : [];
                console.log(`📊 ${title}`);
                console.log(`   ID: ${item.id}`);
                console.log(`   Properties: ${props.length > 0 ? props.join(', ') : '(none - EMPTY)'}`);
                console.log(`   URL: ${item.url}`);
                console.log('');
            }
        });
    });
});

req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
