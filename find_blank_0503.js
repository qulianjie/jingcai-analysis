const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: '2026-05-03' } }, page_size: 100 });
const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); (r.results || []).forEach(p => { const dt = p.properties['比赛日期']?.date?.start; if (!dt || !dt.startsWith('2026-05-03')) return; const n = p.properties.Name?.title?.[0]?.plain_text || ''; if (n.includes('分组统计')) return; const rq = p.properties['让球指数胜']?.number; if (!rq || rq === 0) console.log('BLANK:', n, '| rq=', rq); }); }); });
req.on('error', e => console.error(e)); req.write(data); req.end();
