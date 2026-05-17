const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

// Find missing match for 5-04
const dateDir = path.join(tasksDir, '2026-05-04', 'data');
const dirs = fs.readdirSync(dateDir).filter(d => d.startsWith('match'));
const matchMap = {};
for (const d of dirs) {
    const mp = path.join(dateDir, d, 'meta.json');
    if (fs.existsSync(mp)) {
        const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
        if (m.matchnum) matchMap[m.matchnum] = path.join(dateDir, d);
    }
}

const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: '2026-05-04' } }, page_size: 100 });
const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); const existing = new Set(); (r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith('2026-05-04'); }).forEach(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; const m = n.match(/^([周][一二三四五六日]\d+)/); if (m) existing.add(m[1]); }); for (const [mn, dir] of Object.entries(matchMap)) { if (!existing.has(mn)) console.log('缺失:', mn); } }); });
req.on('error', e => console.error(e)); req.write(data); req.end();
