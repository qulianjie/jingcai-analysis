const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function queryNotionByDate(dateStr) {
    const data = JSON.stringify({
        filter: { and: [
            { property: '比赛日期', date: { on_or_after: dateStr } },
            { property: '比赛日期', date: { on_or_before: dateStr } }
        ]},
        page_size: 100
    });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { try { resolve(JSON.parse(b)); } catch(e) { reject(e); } }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    let total = 0, blank = 0;
    for (let d = 1; d <= 11; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        
        for (const p of pages) {
            const mn = p.properties.Name?.title?.[0]?.plain_text || '';
            const oTrend = p.properties['欧赔趋势']?.rich_text?.[0]?.plain_text || '';
            const mYapan = p.properties['澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            
            total++;
            if (!oTrend || !mYapan) {
                blank++;
                console.log(mn + ' | 欧赔趋势=' + (oTrend || '空白') + ' | 澳门亚盘=' + (mYapan || '空白'));
            }
        }
    }
    console.log('\n总计 ' + total + ' 场，有问题的 ' + blank + ' 场');
}

main().catch(e => console.error(e));
