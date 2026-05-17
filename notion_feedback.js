const https = require('https');

const NOTION_API_KEY = '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';
const DATABASE_ID = '7ee379c2-f436-4d55-8b6b-5b8c48d1b00b';

const feedbackData = [
  { match_num: '001', league: '挪超', home: '维京', away: '罗森博格', score: '3-0', predicted: '平局', actual: '胜', correct: false, confidence: '46%（弱信号）' },
  { match_num: '002', league: '荷乙', home: '瓦尔韦克', away: '罗达JC', score: '1-1', predicted: '平局', actual: '平', correct: true, confidence: '40%（回避信号）' },
  { match_num: '003', league: '意甲', home: '比萨', away: '莱切', score: '1-2', predicted: '平局', actual: '负', correct: false, confidence: '40%（回避信号）' },
  { match_num: '004', league: '英超', home: '利兹联', away: '伯恩利', score: '3-1', predicted: '平局', actual: '胜', correct: false, confidence: '40%（回避信号）' },
  { match_num: '005', league: '西甲', home: '赫罗纳', away: '马洛卡', score: '0-1', predicted: '平局', actual: '负', correct: false, confidence: '40%（回避信号）' },
];

const feedbackDate = '2026-05-01';
const accuracy = '20.0%';
const totalMatches = 5;
const totalCorrect = 1;
const summary = `2026-05-01竞彩反馈：共${totalMatches}场，正确${totalCorrect}场，准确率${accuracy}。`;

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

async function queryExistingPages() {
  const body = {
    filter: {
      property: '反馈日期',
      date: { equals: feedbackDate }
    }
  };
  try {
    const result = await notionRequest('POST', `/v1/databases/${DATABASE_ID}/query`, body);
    return result.results || [];
  } catch (e) {
    console.log('Query error:', e.message);
    return [];
  }
}

async function createPage(match) {
  const page = {
    parent: { database_id: DATABASE_ID },
    properties: {
      'Name': { title: [{ text: { content: `第${match.match_num}场 ${match.league} ${match.home}vs${match.away}` } }] },
      '反馈日期': { date: { start: feedbackDate } },
      '联赛': { select: { name: match.league } },
      '对阵': { rich_text: [{ text: { content: `${match.home}vs${match.away}` } }] },
      '实际比分': { rich_text: [{ text: { content: match.score } }] },
      '实际结果': { select: { name: match.actual } },
      '预测': { select: { name: match.predicted } },
      '预测正确': { checkbox: match.correct },
      '信心': { rich_text: [{ text: { content: match.confidence } }] },
      '反馈总结': { rich_text: [{ text: { content: `预测${match.predicted}→实际${match.actual} ${match.correct ? '✅正确' : '❌错误'}` } }] },
    },
  };
  return notionRequest('POST', '/v1/pages', page);
}

async function createSummaryPage() {
  const page = {
    parent: { database_id: DATABASE_ID },
    properties: {
      'Name': { title: [{ text: { content: `📊 ${feedbackDate} 反馈汇总` } }] },
      '反馈日期': { date: { start: feedbackDate } },
      '反馈总结': { rich_text: [{ text: { content: `共${totalMatches}场，正确${totalCorrect}场，准确率${accuracy}` } }] },
      '预测正确': { checkbox: false },
    },
  };
  return notionRequest('POST', '/v1/pages', page);
}

async function main() {
  console.log('=== 竞彩反馈 → Notion ===');
  console.log(`反馈日期: ${feedbackDate}`);
  console.log(`场次: ${totalMatches}场 | 正确: ${totalCorrect} | 准确率: ${accuracy}`);
  console.log('');

  const existing = await queryExistingPages();
  if (existing.length > 0) {
    console.log(`⚠️ 发现 ${existing.length} 条已存在记录，跳过创建`);
    return;
  }

  console.log('正在创建 Notion 页面...\n');
  for (let i = 0; i < feedbackData.length; i++) {
    const match = feedbackData[i];
    try {
      const result = await createPage(match);
      console.log(`✅ 场次${match.match_num}: ${match.home}vs${match.away} ${match.score} ${match.correct ? '✅' : '❌'}`);
    } catch (e) {
      console.error(`❌ 场次${match.match_num} 失败: ${e.message}`);
    }
  }

  try {
    await createSummaryPage();
    console.log(`\n✅ 汇总页面创建成功`);
  } catch (e) {
    console.error(`❌ 汇总页面创建失败: ${e.message}`);
  }

  console.log('\n=== 完成 ===');
}

main().catch(e => {
  console.error('Fatal error:', e.message);
  process.exit(1);
});
