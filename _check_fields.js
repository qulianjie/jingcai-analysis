const https = require('https');
const KEY = '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';
const body = JSON.stringify({ page_size: 3, filter: { property: '反馈总结', rich_text: { is_not_empty: true } } });
const req = https.request({
  hostname: 'api.notion.com',
  path: '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17/query',
  method: 'POST',
  headers: { 'Authorization': 'Bearer ' + KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
}, res => {
  let d=''; res.on('data',c=>d+=c); res.on('end', () => {
    const r = JSON.parse(d);
    console.log('全部字段:');
    const props = r.results[0]?.properties;
    for (const [k,v] of Object.entries(props)) {
      console.log('  ' + k + ' (' + v.type + ')');
    }
    console.log();
    r.results.slice(0,3).forEach(p => {
      const name = p.properties['Name']?.title?.[0]?.plain_text || '';
      const bestVal = p.properties['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '(空)';
      const rqVal = p.properties['让球预测']?.rich_text?.[0]?.plain_text || '(空)';
      const predVal = p.properties['竞彩预测']?.rich_text?.[0]?.plain_text || '(空)';
      console.log(name);
      console.log('  竞彩预测=' + predVal.substring(0,30));
      console.log('  让球预测=' + rqVal.substring(0,60));
      console.log('  步26_庄家最看好=' + bestVal);
    });
  });
});
req.write(body);
req.end();
