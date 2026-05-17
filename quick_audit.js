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
    let totalGames = 0, totalZeroRq = 0, totalPredicted = 0, totalFeedback = 0;
    
    for (let d = 1; d <= 12; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const results = await queryDate(dateStr);
        const games = results.filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        
        let zeroRq = 0, predicted = 0, feedback = 0, scoreFilled = 0;
        for (const p of games) {
            const rq = p.properties['让球指数胜']?.number;
            const pred = p.properties['竞彩预测']?.rich_text?.[0]?.plain_text;
            const score = p.properties['实际比分']?.rich_text?.[0]?.plain_text;
            const result = p.properties['实际结果']?.rich_text?.[0]?.plain_text;
            
            if (!rq || rq === 0) zeroRq++;
            if (pred) predicted++;
            if (score) { feedback++; if (result) scoreFilled++; }
        }
        
        totalGames += games.length;
        totalZeroRq += zeroRq;
        totalPredicted += predicted;
        totalFeedback += feedback;
        
        console.log(dateStr + ': ' + games.length + '场, 让球0=' + zeroRq + ', 有预测=' + predicted + ', 有比分=' + feedback);
    }
    
    console.log('\n总计: ' + totalGames + '场, 让球0=' + totalZeroRq + ', 有预测=' + totalPredicted + ', 有比分=' + totalFeedback);
}

main().catch(e => console.error(e));
