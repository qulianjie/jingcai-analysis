const https = require('https');
const KEY = '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';
const body = JSON.stringify({ page_size: 3, filter: { property: '反馈总结', rich_text: { is_not_empty: true } } });
const req = https.request({
  hostname: 'api.notion.com',
  path: '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17/query',
  method: 'POST',
  headers: { 'Authorization': 'Bearer ' + KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
}, res => {
  let d='';
  res.on('data',c=>d+=c);
  res.on('end', () => {
    const r = JSON.parse(d);
    r.results.slice(0,3).forEach(p => {
      const name = p.properties['Name']?.title?.[0]?.plain_text || '';
      const pred = p.properties['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const rq = p.properties['让球预测']?.rich_text?.[0]?.plain_text || '';
      const best = p.properties['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const win = p.properties['竞彩欧赔胜']?.number || 0;
      const score = p.properties['实际比分']?.rich_text?.[0]?.plain_text || '';
      console.log(name + ' | 赔率=' + win + ' | 预测=' + pred.substring(0,30) + ' | 让球=' + rq.substring(0,50) + ' | 庄家=' + best.substring(0,10) + ' | 比分=' + score);
    });
  });
});
req.write(body);
req.end();
