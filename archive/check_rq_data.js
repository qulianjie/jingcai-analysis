// 检查让球预测数据
const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const data = JSON.stringify({ page_size: 3, sorts: [{ property: '比赛', direction: 'ascending' }] });

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}/query`,
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        (r.results || []).forEach((p, i) => {
            const pr = p.properties;
            const names = Object.keys(pr);
            console.log(`[${i+1}] Props: ${names.join(', ')}`);
            for (const [k, v] of Object.entries(pr)) {
                if (v.rich_text?.[0]?.plain_text) {
                    console.log(`  ${k}: ${v.rich_text[0].plain_text.substring(0, 50)}`);
                }
            }
        });
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
