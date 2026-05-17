const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

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
    
    for (const dateStr of DATES) {
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        
        console.log('\n=== ' + dateStr + ' (' + pages.length + '场) ===');
        for (const p of pages) {
            const match = p.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            const rqWin = p.properties['让球指数胜']?.number;
            const rqDraw = p.properties['让球指数平']?.number;
            const rqLoss = p.properties['让球指数负']?.number;
            const rqWinEnd = p.properties['终盘让球指数胜']?.number;
            const rqDrawEnd = p.properties['终盘让球指数平']?.number;
            const rqLossEnd = p.properties['终盘让球指数负']?.number;
            const ma = p.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            const maEnd = p.properties['终盘竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            const name = p.properties.Name?.title?.[0]?.plain_text || '';
            const matchCol = p.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            const isWeek = matchCol.startsWith('周');
            console.log('  ' + match + ' ' + name.slice(0, 30) + ' | RQ:' + rqWin + '/' + rqDraw + '/' + rqLoss + ' 终盘:' + rqWinEnd + '/' + rqDrawEnd + '/' + rqLossEnd + ' | MA:' + ma + ' | 比赛列=' + (isWeek ? '✅' : '❌'));
        }
    }
}

main().catch(e => console.error(e));
