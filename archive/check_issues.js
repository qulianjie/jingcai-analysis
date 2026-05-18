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
    const DATES = ['2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05'];
    let issues = 0;
    
    for (const dateStr of DATES) {
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        
        for (const p of pages) {
            const name = p.properties.Name?.title?.[0]?.plain_text || '';
            const match = p.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            
            const rqWin = p.properties['让球指数胜']?.number;
            const rqDraw = p.properties['让球指数平']?.number;
            const rqLoss = p.properties['让球指数负']?.number;
            const rqWinEnd = p.properties['终盘让球指数胜']?.number;
            const rqDrawEnd = p.properties['终盘让球指数平']?.number;
            const rqLossEnd = p.properties['终盘让球指数负']?.number;
            const ma = p.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            const maEnd = p.properties['终盘竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            
            const isUndefined = [rqWin, rqDraw, rqLoss, rqWinEnd, rqDrawEnd, rqLossEnd].some(v => v === undefined || v === null);
            const isAllZero = rqWin === 0 && rqDraw === 0 && rqLoss === 0;
            const isEndAllZero = rqWinEnd === 0 && rqDrawEnd === 0 && rqLossEnd === 0;
            
            if (isUndefined || isAllZero || isEndAllZero) {
                issues++;
                console.log(match + ' | RQ:' + rqWin + '/' + rqDraw + '/' + rqLoss + ' 终盘:' + rqWinEnd + '/' + rqDrawEnd + '/' + rqLossEnd + ' | MA:' + ma + ' | 终盘MA:' + maEnd + (isUndefined ? ' ⚠️ undefined' : '') + (isAllZero && !isUndefined ? ' ⚠️ 全0(竞彩未开)' : '') + (isEndAllZero && !isUndefined ? ' ⚠️ 终盘全0' : ''));
            }
        }
    }
    
    console.log('\n问题记录: ' + issues);
}

main().catch(e => console.error(e));
