// 用data_source查询技术学习日报
const https = require('https');
const API_KEY = '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';
const DS_ID = '2643200f-de7e-47e5-a84a-a31a69257824';

const data = JSON.stringify({ page_size: 100 });

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/data_sources/${DS_ID}/query`,
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
        console.log('Status:', res.statusCode);
        const r = JSON.parse(d);
        console.log('Results:', r.results?.length || 0);
        (r.results || []).forEach((p, i) => {
            console.log(`\n[${i+1}] ID: ${p.id}`);
            const props = p.properties || {};
            for (const [k, v] of Object.entries(props)) {
                if (v.title?.[0]?.plain_text) {
                    console.log(`  ${k}: ${v.title[0].plain_text.substring(0, 100)}`);
                } else if (v.rich_text?.[0]?.plain_text) {
                    console.log(`  ${k}: ${v.rich_text[0].plain_text.substring(0, 100)}`);
                } else if (v.select?.name) {
                    console.log(`  ${k}: ${v.select.name}`);
                } else if (v.date?.start) {
                    console.log(`  ${k}: ${v.date.start}`);
                } else if (v.checkbox !== undefined) {
                    console.log(`  ${k}: ${v.checkbox}`);
                }
            }
        });
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
