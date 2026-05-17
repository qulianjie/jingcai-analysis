const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const tasksDir = path.join(__dirname, 'tasks');

// Check 5-01, 5-02, 5-07 records
async function checkDate(dateStr) {
    const data = JSON.stringify({
        filter: {
            and: [
                { property: '比赛日期', date: { on_or_after: dateStr } },
                { property: '比赛日期', date: { before: dateStr.replace(/-(\d\d)$/, m => '-' + String(parseInt(m.slice(1))+1).padStart(2,'0')) } }
            ]
        },
        page_size: 100
    });
    // Simpler approach: just query and filter
    const data2 = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: dateStr } }, page_size: 100 });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data2) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); const filtered = (r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith(dateStr); }); resolve(filtered); }); });
        req.on('error', reject); req.write(data2); req.end();
    });
}

function updatePage(pageId, props) {
    const data = JSON.stringify({ properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages/' + pageId, method: 'PATCH', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b)); else resolve(JSON.parse(b)); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    const dates = ['2026-05-01','2026-05-02','2026-05-07'];
    for (const dateStr of dates) {
        const results = await checkDate(dateStr);
        const games = results.filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        let zeroRq = 0;
        for (const p of games) {
            const rq = p.properties['让球指数胜']?.number;
            if (!rq || rq === 0) {
                const n = p.properties.Name?.title?.[0]?.plain_text || '';
                console.log('  ZERO RQ:', n);
                zeroRq++;
            }
        }
        console.log(dateStr + ': ' + games.length + '场, 让球0: ' + zeroRq);
    }
}

main().catch(e => console.error(e));
