const https = require('https');
const KEY = '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';
const body = JSON.stringify({ page_size: 3 });

const req = https.request({
  hostname: 'api.notion.com',
  path: '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17/query',
  method: 'POST',
  headers: { 'Authorization': 'Bearer ' + KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
}, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    const r = JSON.parse(d);
    if (!r.results || r.results.length === 0) { console.log('无数据'); return; }
    const p = r.results[0];
    console.log('Name:', p.properties['Name']?.title?.[0]?.plain_text);
    console.log('=== 所有字段 ===');
    for (const [k, v] of Object.entries(p.properties)) {
      const type = Object.keys(v).find(kk => kk !== 'id' && kk !== 'type') || '?';
      let val = '?';
      if (v[type] && typeof v[type] === 'object' && v[type].length > 0) {
        val = v[type][0]?.plain_text || v[type][0]?.name || JSON.stringify(v[type][0]).substring(0, 80);
      } else if (v[type] && typeof v[type] === 'object' && !Array.isArray(v[type])) {
        val = v[type]?.name || v[type]?.start || JSON.stringify(v[type]).substring(0, 80);
      } else {
        val = String(v[type]).substring(0, 80);
      }
      console.log('  [' + k + '] type=' + v.type + ' val=' + val);
    }
  });
});
req.write(body);
req.end();
