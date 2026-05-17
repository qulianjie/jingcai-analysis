const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

async function queryDate(dateStr) {
    const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: dateStr } }, page_size: 100 });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); resolve((r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith(dateStr); })); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    const dates = ['2026-05-03','2026-05-04','2026-05-09','2026-05-10','2026-05-11','2026-05-12'];
    for (const d of dates) {
        const results = await queryDate(d);
        const games = results.filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        let zeroRq = 0, zeroMa = 0;
        const zeros = [];
        for (const p of games) {
            const rq = p.properties['让球指数胜']?.number;
            const ma = p.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text;
            if (!rq || rq === 0) { zeroRq++; const n = p.properties.Name?.title?.[0]?.plain_text || ''; zeros.push(n); }
            if (!ma) zeroMa++;
        }
        console.log(d + ': ' + games.length + '场, 让球0:' + zeroRq + ', 澳门空白:' + zeroMa);
        if (zeros.length <= 10) zeros.forEach(z => console.log('  - ' + z));
    }
}

main().catch(e => console.error(e));
