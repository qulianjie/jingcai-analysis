// Check Notion database structure
const https = require('https');
const NOTION_API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fba45ccb6471eaf4d9';

function notionGet(path) {
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.notion.com',
      path,
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Notion-Version': '2022-06-28',
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
    req.end();
  });
}

(async () => {
  const r = await notionGet('/v1/databases/' + DB_ID);
  console.log('Status:', r.status);
  console.log('Response:', JSON.stringify(r.data, null, 2).substring(0, 500));
  console.log('DB Name:', r.data.title?.[0]?.plain_text || r.data.name || '?');
  const props = r.data.properties;
  const keys = Object.keys(props);
  console.log('Properties (' + keys.length + '):');
  keys.forEach(k => {
    console.log('  ' + k + ' -> ' + props[k].type);
  });
})();
