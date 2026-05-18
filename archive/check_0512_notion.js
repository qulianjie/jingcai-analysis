const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const data = JSON.stringify({
  filter: {
    property: '比赛日期',
    date: { on_or_after: '2026-05-12' }
  },
  page_size: 50
});

const req = https.request({
  hostname: 'api.notion.com',
  path: '/v1/databases/' + DB_ID + '/query',
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + API_KEY,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data)
  }
}, res => {
  let b = '';
  res.on('data', c => b += c);
  res.on('end', () => {
    const r = JSON.parse(b);
    if (r.results) {
      r.results.forEach(p => {
        const n = p.properties.Name?.title?.[0]?.plain_text || '';
        if (n.includes('分组统计')) return;
        const rq = p.properties['竞彩让球指数']?.rich_text?.[0]?.plain_text || '(空)';
        const ma = p.properties['澳门亚盘']?.rich_text?.[0]?.plain_text || '(空)';
        console.log(n, '| RQ:', rq, '| MA:', ma);
      });
    } else {
      console.log(JSON.stringify(r).slice(0, 200));
    }
  });
});
req.on('error', e => console.error(e));
req.write(data);
req.end();
