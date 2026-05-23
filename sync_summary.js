/**
 * sync_summary.js — 从竞彩比赛追踪全量统计 → 刷新历史汇总Notion数据库
 * 
 * 执行时机：feedback.js 每次跑完后自动调用
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = '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';
const MATCH_DB = '35491ad7-17ba-81cc-aa04-ce53f7234e17';   // 竞彩比赛追踪（数据源）
const SUMMARY_DB = '35d91ad717ba802facb7ebfd74db132c';     // 历史汇总（目标）

// ===== Notion API 工具 =====
async function request(method, path, body) {
  return new Promise((rs, rj) => {
    const opts = {
      hostname: 'api.notion.com',
      path: path,
      method: method,
      headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
      }
    };
    if (body) opts.headers['Content-Length'] = Buffer.byteLength(body);
    const req = https.request(opts, res => {
      let d = '';
      res.on('data', x => d += x);
      res.on('end', () => rs(JSON.parse(d)));
    });
    req.on('error', rj);
    req.setTimeout(15000, () => { req.destroy(); rj(new Error('timeout')); });
    if (body) req.write(body);
    req.end();
  });
}

async function getAllPages(dbId, filter) {
  let all = [], cursor;
  while (true) {
    const body = JSON.stringify({ page_size: 100, start_cursor: cursor, ...(filter ? { filter } : {}) });
    const r = await request('POST', '/v1/databases/' + dbId + '/query', body);
    all = all.concat(r.results || []);
    cursor = r.next_cursor;
    if (!cursor) break;
    await sleep(300);
  }
  return all;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ===== 从竞彩追踪统计 =====
function generateGroupsFromMatches(matches) {
  const groups = {};

  for (const p of matches) {
    const props = p.properties;
    
    // 竞彩预测方向
    const jcPred = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
    let jcResult = null;
    if (jcPred.includes('主胜')) jcResult = '主胜';
    else if (jcPred.includes('客胜')) jcResult = '客胜';
    else if (jcPred.includes('平局')) jcResult = '平局';

    // 庄家方向(步26)
    const zjText = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
    let zjResult = null;
    if (zjText.includes('主胜')) zjResult = '主胜';
    else if (zjText.includes('客胜')) zjResult = '客胜';
    else if (zjText.includes('平局')) zjResult = '平局';

    // 让球预测方向
    const rqPred = props['让球预测']?.rich_text?.[0]?.plain_text || '';
    const rqNumMatch = rqPred.match(/(受让\d+球|让[+-]?\d+(?:\.5)?球|平手)/);
    const rqNumPart = rqNumMatch ? rqNumMatch[1] : '';
    let rqResult = null;
    if (rqPred.includes('让球主胜') || rqPred.includes('让球胜')) {
      rqResult = rqNumPart ? rqNumPart + ' 主胜' : '让球主胜';
    } else if (rqPred.includes('让球客胜')) {
      rqResult = rqNumPart ? rqNumPart + ' 客胜' : '让球客胜';
    } else if (rqPred.includes('让球平')) {
      rqResult = rqNumPart ? rqNumPart + ' 平' : '让球平';
    }

    // 实际结果
    const actualResult = props['实际结果']?.rich_text?.[0]?.plain_text || '';
    if (!actualResult) continue; // 没有实际结果的跳过

    // 过滤：三个维度至少有一个有预测
    if (!jcResult && !zjResult && !rqResult) continue;

    const groupKey = (jcResult || '未知') + '|' + (zjResult || '未知') + '|' + (rqResult || '未知');

    if (!groups[groupKey]) {
      groups[groupKey] = { total: 0, 胜: 0, 平: 0, 负: 0, 让球胜: 0, 让球平: 0, 让球负: 0 };
    }
    groups[groupKey].total++;
    groups[groupKey][actualResult]++;

    // 让球实际结果（用实际比分 + 让球预测中的让球数反推）
    const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
    if (score && rqPred) {
      const scoreParts = score.split(':');
      if (scoreParts.length === 2) {
        let homeScore = parseInt(scoreParts[0]);
        let awayScore = parseInt(scoreParts[1]);
        
        if (!isNaN(homeScore) && !isNaN(awayScore)) {
          // 从让球预测提取让球数
          const rqNumMatch = rqPred.match(/(受让)(\d+(?:\.5)?)球/);
          if (rqNumMatch) {
            // 受让X球：客队让球，主队受让
            const handicap = parseFloat(rqNumMatch[2]);
            if (!isNaN(handicap)) {
              homeScore += handicap; // 主队受让，加分
            }
          } else {
            // 让X球：主队让球（不计平手/无让球情况）
            const rqNumMatch2 = rqPred.match(/让(\d+(?:\.5)?)球/);
            if (rqNumMatch2 && !rqPred.startsWith('受让')) {
              const handicap = parseFloat(rqNumMatch2[1]);
              if (!isNaN(handicap)) {
                awayScore += handicap; // 主队让球，客队加分
              }
            }
          }
          
          // 计算让球后实际结果
          if (homeScore > awayScore) groups[groupKey]['让球胜']++;
          else if (homeScore < awayScore) groups[groupKey]['让球负']++;
          else groups[groupKey]['让球平']++;
        }
      }
    }
  }

  return groups;
}

// ===== 写入历史汇总 Notion =====
async function writeSummary(groups) {
  console.log('清空旧数据...');

  // 获取所有旧记录
  const oldPages = await getAllPages(SUMMARY_DB);
  console.log('  旧数据:', oldPages.length, '条');

  // 删除旧记录（归档）
  let deleted = 0;
  for (const p of oldPages) {
    try {
      await request('PATCH', '/v1/pages/' + p.id, JSON.stringify({ archived: true }));
      deleted++;
    } catch (e) {
      console.log('  ❌ 删除失败:', e.message);
    }
    if (deleted % 20 === 0 && deleted > 0) {
      console.log('  ...已清空', deleted, '条');
    }
    await sleep(300);
  }
  console.log('  已清空:', deleted, '条');

  console.log('\n写入新数据...');

  // 写入汇总行（总计）
  let total = 0, totalWin = 0, totalDraw = 0, totalLoss = 0;
  let totalRqWin = 0, totalRqDraw = 0, totalRqLoss = 0;
  
  for (const stats of Object.values(groups)) {
    total += stats.total;
    totalWin += stats.胜;
    totalDraw += stats.平;
    totalLoss += stats.负;
    totalRqWin += stats.让球胜 || 0;
    totalRqDraw += stats.让球平 || 0;
    totalRqLoss += stats.让球负 || 0;
  }

  // 汇总行
  try {
    const summaryRow = {
      parent: { database_id: SUMMARY_DB },
      properties: {
        '竞彩': { title: [{ text: { content: '📊 汇总' } }] },
        '场数': { number: total },
        '胜': { number: totalWin },
        '平': { number: totalDraw },
        '负': { number: totalLoss },
        '让球胜': { number: totalRqWin },
        '让球平': { number: totalRqDraw },
        '让球负': { number: totalRqLoss },
      }
    };
    await request('POST', '/v1/pages', JSON.stringify(summaryRow));
    console.log('  ✅ 汇总行: ' + total + '场 胜' + totalWin + ' 平' + totalDraw + ' 负' + totalLoss);
  } catch (e) {
    console.log('  ❌ 汇总行失败:', e.message);
  }

  // 分组明细行（按总场数降序）
  const sorted = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);

  let written = 0;
  for (const [key, stats] of sorted) {
    const [pred, zj, rq] = key.split('|');

    try {
      const row = {
        parent: { database_id: SUMMARY_DB },
        properties: {
          '竞彩': { title: [{ text: { content: pred || '未知' } }] },
          '庄家': zj ? { select: { name: zj } } : undefined,
          '让球': rq ? { select: { name: rq } } : undefined,
          '场数': { number: stats.total },
          '胜': { number: stats.胜 },
          '平': { number: stats.平 },
          '负': { number: stats.负 },
          '让球胜': { number: stats.让球胜 || 0 },
          '让球平': { number: stats.让球平 || 0 },
          '让球负': { number: stats.让球负 || 0 },
        }
      };
      // 清理undefined
      const cleanProps = {};
      Object.entries(row.properties).forEach(([k, v]) => { if (v !== undefined) cleanProps[k] = v; });
      row.properties = cleanProps;

      await request('POST', '/v1/pages', JSON.stringify(row));
      written++;
    } catch (e) {
      console.log('  ❌ 写入失败:', key, e.message);
    }

    if (written % 10 === 0) console.log('  ...已写入', written, '条');
    await sleep(400);
  }

  console.log('  ✅ 分组明细: ' + written + ' 条');
  console.log(`\n📊 总计: ${total}场 | 胜${totalWin} 平${totalDraw} 负${totalLoss} | 让球胜${totalRqWin} 让球平${totalRqDraw} 让球负${totalRqLoss}`);
}

// ===== 主流程 =====
async function main() {
  console.log('=== 同步历史汇总 ===\n');

  console.log('[1/3] 获取竞彩比赛追踪数据...');
  const allMatches = await getAllPages(MATCH_DB, null);
  const validMatches = allMatches.filter(p => {
    const n = p.properties.Name?.title?.[0]?.plain_text || '';
    return !n.includes('分组统计') && !n.includes('汇总');
  });
  console.log('  有效比赛:', validMatches.length, '条');

  console.log('[2/3] 分组统计...');
  const groups = generateGroupsFromMatches(validMatches);
  console.log('  分组数:', Object.keys(groups).length);

  // 打印简表
  const sorted = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);
  console.log('\n预测分组 | 庄家 | 让球 | 场数 | 胜/平/负');
  for (const [key, stats] of sorted.slice(0, 10)) {
    const [pred, zj, rq] = key.split('|');
    console.log(`  ${pred} | ${zj} | ${rq} | ${stats.total} | ${stats.胜}/${stats.平}/${stats.负}`);
  }
  if (sorted.length > 10) console.log('  ...共', sorted.length, '组');

  console.log('\n[3/3] 写入历史汇总 Notion...');
  await writeSummary(groups);

  console.log('\n✅ 同步完成');
}

main().catch(err => {
  console.error('[FATAL]', err.message);
  process.exit(1);
});
