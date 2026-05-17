const https = require('https');

const NOTION_API_KEY = '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';
const DATABASE_ID = '7ee379c2-f436-4d55-8b6b-5b8c48d1b00b';

const schemaUpdate = {
  properties: {
    '反馈日期': { type: 'date', date: {} },
    '实际比分': { type: 'rich_text', rich_text: {} },
    '实际结果': { type: 'select', select: { options: [
      { name: '胜' }, { name: '平' }, { name: '负' }
    ]}},
    '预测': { type: 'select', select: { options: [
      { name: '胜' }, { name: '平' }, { name: '负' }, { name: '平局' }
    ]}},
    '预测正确': { type: 'checkbox', checkbox: {} },
    '联赛': { type: 'select', select: { options: [] }},
    '对阵': { type: 'rich_text', rich_text: {} },
    '信心': { type: 'rich_text', rich_text: {} },
    '反馈总结': { type: 'rich_text', rich_text: {} },
  }
};

function notionRequest(method, path, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: 'api.notion.com',
      path: path,
      method: method,
      headers: {
        'Authorization': `Bearer ${NOTION_API_KEY}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      },
    };
    if (data) options.headers['Content-Length'] = Buffer.byteLength(data);

    const req = https.request(options, (res) => {
      let chunks = '';
      res.on('data', (chunk) => chunks += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(chunks);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            console.log(`✅ ${method} ${path}: OK`);
            resolve(json);
          } else {
            reject(new Error(`Notion API ${res.statusCode}: ${chunks}`));
          }
        } catch (e) {
          reject(new Error(`Parse error ${res.statusCode}: ${chunks}`));
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function main() {
  console.log('=== 更新 Notion 数据库 schema ===');
  try {
    await notionRequest('PATCH', `/v1/databases/${DATABASE_ID}`, schemaUpdate);
    console.log('\n✅ 数据库 schema 更新完成');
    console.log('新增属性: 反馈日期, 实际比分, 实际结果, 预测, 预测正确, 联赛, 对阵, 信心, 反馈总结');
  } catch (e) {
    console.error('❌ Schema 更新失败:', e.message);
    process.exit(1);
  }
}

main();
