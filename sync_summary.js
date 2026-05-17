const https = require('https');
const apiKey = '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';

const MATCH_DB = '35491ad7-17ba-81cc-aa04-ce53f7234e17'; // 竞彩比赛追踪
const SUMMARY_DB = '35d91ad7-17ba-802f-acb7-ebfd74db132c'; // 历史汇总

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

/**
 * 从反馈总结提取让球胜平负（实际让球后的结果）
 */
function extractRqResult(summary) {
  if (!summary) return null;
  // Match: 让球让1球: ... → 胜 or 让球受让1球: ... → 胜
  const match = summary.match(/让球[让受让]让?\d+球.*?→\s*([胜平负])/);
  return match ? match[1] : null;
}

/**
 * 从反馈总结提取让球胜平负（实际让球后的结果）
 */
function extractRqResult(summary) {
  if (!summary) return null;
  // Match: 让球让1球: ... → 胜 or 让球受让1球: ... → 胜
  const match = summary.match(/让球[让受让]让?\d+球.*?→\s*([胜平负])/);
  return match ? match[1] : null;
}

/**
 * 从让球预测提取方向（主胜/客胜/平）
 */
function extractRqPrediction(text) {
  if (!text) return null;
  if (text.includes('让球主胜') || text.includes('让球胜')) return '胜';
  if (text.includes('让球客胜') || text.includes('让球负')) return '负';
  if (text.includes('让球平')) return '平';
  return null;
}

/**
 * 从竞彩预测提取方向（只保留 主胜/平局/客胜）
 */
function extractPrediction(text) {
  if (!text) return '未知';
  if (text.includes('主胜')) return '主胜';
  if (text.includes('客胜')) return '客胜';
  if (text.includes('平局')) return '平局';
  return '未知';
}

/**
 * 从庄家最看好提取方向
 */
function extractBanker(text) {
  if (!text) return '未知';
  if (text.includes('主胜')) return '主胜';
  if (text.includes('客胜')) return '客胜';
  if (text.includes('平局')) return '平局';
  return '未知';
}

/**
 * 从让球预测提取（如：让1球 让球客胜 → "让1球 客胜"）
 */
function extractHandicap(text) {
  if (!text) return '未知';
  // 提取让球数
  const numMatch = text.match(/(受让\d+球|让[+-]?\d+(?:\.5)?球)/);
  const numPart = numMatch ? numMatch[1] : '';
  // 提取方向
  if (text.includes('让球主胜') || text.includes('让球胜')) {
    return numPart ? `${numPart} 主胜` : '未知';
  }
  if (text.includes('让球客胜') || text.includes('让球负')) {
    return numPart ? `${numPart} 客胜` : '未知';
  }
  if (text.includes('让球平')) {
    return numPart ? `${numPart} 平` : '未知';
  }
  return '未知';
}

/**
 * 从实际结果提取胜平负
 */
function extractResult(text) {
  if (!text) return null;
  if (text.includes('胜')) return '胜';
  if (text.includes('负')) return '负';
  if (text.includes('平')) return '平';
  return null;
}

/**
 * 分页查询所有匹配的比赛
 */
async function queryAllMatches(filter) {
  let allResults = [];
  let startCursor = null;
  
  do {
    const body = {
      filter,
      page_size: 100,
      ...(startCursor ? { start_cursor: startCursor } : {}),
    };
    const res = await notionRequest('POST', `/v1/databases/${MATCH_DB}/query`, body);
    allResults = allResults.concat(res.data.results || []);
    startCursor = res.data.has_more ? res.data.next_cursor : null;
  } while (startCursor);
  
  return allResults;
}

/**
 * 删除历史汇总所有记录
 */
async function clearSummary() {
  console.log('正在清空历史汇总数据库...');
  let allResults = [];
  let startCursor = null;
  do {
    const body = { page_size: 100, ...(startCursor ? { start_cursor: startCursor } : {}) };
    const res = await notionRequest('POST', `/v1/databases/${SUMMARY_DB}/query`, body);
    allResults = allResults.concat(res.data.results || []);
    startCursor = res.data.has_more ? res.data.next_cursor : null;
  } while (startCursor);
  
  const delPromises = allResults.map(page => {
    return notionRequest('PATCH', `/v1/pages/${page.id}`, { archived: true });
  });
  await Promise.all(delPromises);
  console.log(`已清空 ${allResults.length} 条记录`);
}

/**
 * 写入汇总记录
 */
async function insertSummary(groups) {
  console.log(`正在写入 ${Object.keys(groups).length} 条汇总记录...`);
  
  const promises = Object.entries(groups).map(([key, stats]) => {
    const [pred, banker, handicap] = key.split('|');
    const data = {
      parent: { database_id: SUMMARY_DB },
      properties: {
        '竞彩': { title: [{ text: { content: pred } }] },
        '庄家': { select: { name: banker } },
        '让球': { select: { name: handicap } },
        '场数': { number: stats.total },
        '胜': { number: stats.胜 },
        '平': { number: stats.平 },
        '负': { number: stats.负 },
        '让球胜': { number: stats.让球胜 || 0 },
        '让球平': { number: stats.让球平 || 0 },
        '让球负': { number: stats.让球负 || 0 },
      },
    };
    return notionRequest('POST', '/v1/pages', data);
  });
  
  await Promise.all(promises);
  console.log('写入完成');
}

async function main() {
  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];
  
  const CUTOFF_DATE = '2026-05-07'; // 只统计此日期及以后
  console.log(`日期范围: ${CUTOFF_DATE} ~ ${todayStr}（不含当天）\n`);
  
  // 1. 查询 >= 5月7日 且 < 今天 的所有比赛
  console.log('[1/3] 读取竞彩比赛追踪明细...');
  const filter = {
    and: [
      { property: '比赛日期', date: { on_or_after: CUTOFF_DATE } },
      { property: '比赛日期', date: { before: todayStr } },
    ]
  };
  const matches = await queryAllMatches(filter);
  console.log(`找到 ${matches.length} 场比赛（${CUTOFF_DATE} ~ ${todayStr}）`);
  
  // 2. 按 竞彩+庄家+让球 分组统计实际结果 + 让球胜平负
  console.log('\n[2/3] 分组统计...');
  const groups = {};
  let matched = 0, skipped = 0;
  
  for (const page of matches) {
    const props = page.properties;
    const pred = extractPrediction(props['竞彩预测']?.rich_text?.[0]?.plain_text);
    const banker = extractBanker(props['步26_庄家最看好']?.rich_text?.[0]?.plain_text);
    const handicap = extractHandicap(props['让球预测']?.rich_text?.[0]?.plain_text);
    const actualScore = props['实际比分']?.rich_text?.[0]?.plain_text || '';
    
    // 没有比分的跳过
    if (!actualScore || !actualScore.match(/\d+:\d+/)) {
      skipped++;
      continue;
    }
    
    const result = extractResult(props['实际结果']?.rich_text?.[0]?.plain_text);
    
    // 没有实际结果的跳过
    if (!result) {
      skipped++;
      continue;
    }
    
    // 从反馈总结提取让球实际结果（胜/平/负）
    const summary = props['反馈总结']?.rich_text?.[0]?.plain_text || '';
    const rqResult = extractRqResult(summary);
    
    // 竞彩预测或庄家最看好为空的跳过（无法分组）
    if (pred === '未知' || banker === '未知') {
      skipped++;
      continue;
    }
    
    // 竞彩预测或庄家最看好为空的跳过（无法分组）
    if (pred === '未知' || banker === '未知') {
      skipped++;
      continue;
    }
    
    const key = `${pred}|${banker}|${handicap}`;
    if (!groups[key]) {
      groups[key] = { total: 0, 胜: 0, 平: 0, 负: 0, 让球胜: 0, 让球平: 0, 让球负: 0 };
    }
    groups[key].total++;
    groups[key][result]++;
    
    // 统计让球胜平负（按反馈总结里的让球实际结果）
    if (rqResult) {
      groups[key]['让球' + rqResult]++;
    }
    matched++;
  }
  
  console.log(`有效比赛: ${matched} 场（已统计）`);
  console.log(`跳过: ${skipped} 场（无实际结果）`);
  console.log(`分组数: ${Object.keys(groups).length}\n`);
  
  // 按场数排序打印
  const sorted = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);
  console.log('📊 分组统计:');
  console.log('| 竞彩 | 庄家 | 让球 | 场数 | 胜 | 平 | 负 |');
  console.log('|------|------|------|------|------|------|------|');
  for (const [key, stats] of sorted) {
    const [pred, banker, handicap] = key.split('|');
    console.log(`| ${pred} | ${banker} | ${handicap} | ${stats.total} | ${stats.胜} | ${stats.平} | ${stats.负} |`);
  }
  
  // 3. 清空历史汇总并重新写入
  console.log('\n[3/3] 更新历史汇总数据库...');
  await clearSummary();
  await insertSummary(groups);
  
  console.log('\n✅ 历史汇总刷新完成');
}

main().catch(e => {
  console.error('❌ 错误:', e.message);
  process.exit(1);
});
