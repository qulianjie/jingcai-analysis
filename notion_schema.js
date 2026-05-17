const https = require('https');

const NOTION_API_KEY = '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';
const DATABASE_ID = '7ee379c2-f436-4d55-8b6b-5b8c48d1b00b';

const options = {
  hostname: 'api.notion.com',
  path: `/v1/databases/${DATABASE_ID}`,
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${NOTION_API_KEY}`,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
  },
};

const req = https.request(options, (res) => {
  let chunks = '';
  res.on('data', (chunk) => chunks += chunk);
  res.on('end', () => {
    console.log(chunks);
  });
});
req.on('error', (e) => console.error(e));
req.end();
