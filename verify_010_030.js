// 验证010-030数据
const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const data = JSON.stringify({ page_size: 30, sorts: [{ property: '比赛', direction: 'ascending' }] });

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
        console.log(`共 ${r.results?.length || 0} 条\n`);
        let hasRq = 0, noRq = 0;
        (r.results || []).forEach((p, i) => {
            const pr = p.properties;
            const match = pr['比赛']?.rich_text?.[0]?.plain_text || '?';
            const pred = pr['竞彩预测']?.rich_text?.[0]?.plain_text || '(空)';
            const rq = pr['让球预测']?.rich_text?.[0]?.plain_text || '(空)';
            if (rq !== '(空)') hasRq++; else noRq++;
            // 只显示010-030
            const num = match.match(/(\d{3})/)?.[1];
            if (num && parseInt(num) >= 10) {
                console.log(`${match}`);
                console.log(`   竞彩: ${pred} | 让球: ${rq.substring(0, 30)}`);
            }
        });
        console.log(`\n让球预测有数据: ${hasRq} | 无数据: ${noRq}`);
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
