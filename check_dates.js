const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// Query all records, check date formats
const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: '2026-05-01' } }, page_size: 200 });
const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); const dates = {}; (r.results || []).forEach(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; if (n.includes('分组统计')) return; const dt = p.properties['比赛日期']?.date?.start || 'NO_DATE'; const key = dt.substring(0, 10); dates[key] = (dates[key] || 0) + 1; }); for (const k of Object.keys(dates).sort()) console.log(k + ': ' + dates[k]); console.log('total: ' + r.results.length); }); });
req.on('error', e => console.error(e)); req.write(data); req.end();
