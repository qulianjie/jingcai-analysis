const https = require('https');
const API_KEY = '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';
const DB_ID = 'aa554c81-1ff8-497c-88b1-c04eecc383ff';

const data = JSON.stringify({ page_size: 5 });

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}/query`,
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
        console.log('Status:', res.statusCode);
        console.log('Total:', r.results?.length || 0);
        if (r.message) console.log('Error:', r.message);
        
        (r.results || []).forEach((p, i) => {
            const props = p.properties;
            const names = Object.keys(props || {});
            console.log(`\n[${i+1}] Props: ${names.length} - ${names.join(', ')}`);
            for (const [k, v] of Object.entries(props || {})) {
                if (v.rich_text?.[0]?.plain_text) {
                    const val = v.rich_text[0].plain_text.substring(0, 60);
                    console.log(`  ${k}: ${val}`);
                } else if (v.select?.name) {
                    console.log(`  ${k}: ${v.select.name}`);
                }
            }
        });
    });
});

req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
