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
    const summary = {};
    
    for (let d = 1; d <= 11; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        
        let rqBlank = 0, rqEndBlank = 0, maBlank = 0, maEndBlank = 0;
        let allOk = 0;
        
        for (const p of pages) {
            const mn = p.properties.Name?.title?.[0]?.plain_text || '';
            const matchCol = p.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            
            const rqWin = p.properties['让球指数胜']?.number;
            const rqDraw = p.properties['让球指数平']?.number;
            const rqLoss = p.properties['让球指数负']?.number;
            const rqWinEnd = p.properties['终盘让球指数胜']?.number;
            const rqDrawEnd = p.properties['终盘让球指数平']?.number;
            const rqLossEnd = p.properties['终盘让球指数负']?.number;
            const ma = p.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            const maEnd = p.properties['终盘竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            
            const isRqBlank = (rqWin === undefined || rqWin === null) || (rqDraw === undefined || rqDraw === null) || (rqLoss === undefined || rqLoss === null);
            const isRqEndBlank = (rqWinEnd === undefined || rqWinEnd === null) || (rqDrawEnd === undefined || rqDrawEnd === null) || (rqLossEnd === undefined || rqLossEnd === null);
            const isMaBlank = !ma;
            const isMaEndBlank = !maEnd;
            
            if (isRqBlank) { rqBlank++; console.log('  ⚠️ ' + mn + ' 让球指数空白'); }
            if (isRqEndBlank) { rqEndBlank++; console.log('  ⚠️ ' + mn + ' 终盘让球指数空白'); }
            if (isMaBlank) { maBlank++; console.log('  ⚠️ ' + mn + ' 竞彩澳门亚盘空白'); }
            if (isMaEndBlank) { maEndBlank++; console.log('  ⚠️ ' + mn + ' 终盘竞彩澳门亚盘空白'); }
            
            if (!isRqBlank && !isRqEndBlank && !isMaBlank && !isMaEndBlank) {
                allOk++;
            }
        }
        
        summary[dateStr] = {
            total: pages.length,
            ok: allOk,
            rqBlank,
            rqEndBlank,
            maBlank,
            maEndBlank
        };
        
        console.log(dateStr + ': ' + pages.length + '场 | 全部✅=' + allOk + ' | 让球空白=' + rqBlank + ' | 终盘让球空白=' + rqEndBlank + ' | MA空白=' + maBlank + ' | 终盘MA空白=' + maEndBlank);
    }
    
    console.log('\n=== 汇总 ===');
    let totalOk = 0, totalRqBlank = 0, totalRqEndBlank = 0, totalMaBlank = 0, totalMaEndBlank = 0;
    for (const [date, s] of Object.entries(summary)) {
        totalOk += s.ok;
        totalRqBlank += s.rqBlank;
        totalRqEndBlank += s.rqEndBlank;
        totalMaBlank += s.maBlank;
        totalMaEndBlank += s.maEndBlank;
    }
    console.log('全部✅: ' + totalOk);
    console.log('让球指数空白: ' + totalRqBlank);
    console.log('终盘让球指数空白: ' + totalRqEndBlank);
    console.log('竞彩澳门亚盘空白: ' + totalMaBlank);
    console.log('终盘竞彩澳门亚盘空白: ' + totalMaEndBlank);
}

main().catch(e => console.error(e));
