const https = require('https');

const NOTION_API_KEY = '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';
const DATABASE_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const STEPS_DATABASE_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
        catch (e) { resolve({ status: res.statusCode, data: d }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function main() {
  console.log('=== 主数据库字段 ===');
  const r1 = await notionRequest('GET', '/v1/databases/' + DATABASE_ID);
  if (r1.status === 200 && r1.data.properties) {
    for (const [name, prop] of Object.entries(r1.data.properties)) {
      console.log('  ' + name + ' (' + prop.type + ')');
    }
  } else {
    console.log('  ERROR: ' + r1.status + ' ' + JSON.stringify(r1.data).substring(0, 300));
  }

  console.log('');
  console.log('=== 26步数据库字段 ===');
  const r2 = await notionRequest('GET', '/v1/databases/' + STEPS_DATABASE_ID);
  if (r2.status === 200 && r2.data.properties) {
    for (const [name, prop] of Object.entries(r2.data.properties)) {
      console.log('  ' + name + ' (' + prop.type + ')');
    }
  } else {
    console.log('  ERROR: ' + r2.status + ' ' + JSON.stringify(r2.data).substring(0, 300));
  }
}

main().catch(e => console.error(e));
