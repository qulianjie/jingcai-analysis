const https = require('https');
const apiKey = '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';
const dbId = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': 'Bearer ' + apiKey,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, data: JSON.parse(d) }));
    });
    if (body) req.write(body);
    req.end();
  });
}

async function main() {
  const res = await notionRequest('POST', '/v1/databases/' + dbId + '/query', {
    sorts: [{ property: '日期', direction: 'ascending' }],
    page_size: 100
  });
  
  const byDate = {};
  for (const page of res.data.results) {
    const p = page.properties;
    const date = p['日期']?.title?.[0]?.plain_text || '(空)';
    if (!byDate[date]) byDate[date] = 0;
    byDate[date]++;
  }
  
  console.log('历史每日汇总数据库 - 各日期记录数:');
  for (const [date, count] of Object.entries(byDate).sort()) {
    console.log('  ' + date + ': ' + count + ' 条记录');
  }
  
  // Check for '竞彩:未知' records
  console.log('\n含"未知"的记录:');
  for (const page of res.data.results) {
    const p = page.properties;
    const jc = p['竞彩']?.select?.name || '';
    if (jc === '未知') {
      const date = p['日期']?.title?.[0]?.plain_text || '';
      const zj = p['庄家']?.select?.name || '';
      const rq = p['让球']?.select?.name || '';
      console.log('  日期=' + date + ' | 庄家=' + zj + ' | 让球=' + rq);
    }
  }
}

main();
