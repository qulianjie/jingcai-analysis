const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// Query all records from 5-01 onwards
const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: '2026-05-01' } }, page_size: 200 });
const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); const byDate = {}; (r.results || []).forEach(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; if (n.includes('分组统计')) return; const dt = p.properties['比赛日期']?.date?.start || 'no-date'; const key = dt.substring(0, 10); if (!byDate[key]) byDate[key] = { total: 0, zeroRq: 0, zeroMa: 0, zeros: [] }; byDate[key].total++; const rq = p.properties['让球指数胜']?.number; const ma = p.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text; if (!rq || rq === 0) { byDate[key].zeroRq++; byDate[key].zeros.push(n); } if (!ma) byDate[key].zeroMa++; }); for (const k of Object.keys(byDate).sort()) { const v = byDate[k]; console.log(k + ': ' + v.total + '场, 让球0:' + v.zeroRq + ', 澳门空白:' + v.zeroMa); if (v.zeroRq > 0 && v.zeroRq <= 10) v.zeros.forEach(z => console.log('  - ' + z)); } console.log('\n总计: ' + r.results.length + '条'); }); });
req.on('error', e => console.error(e)); req.write(data); req.end();
