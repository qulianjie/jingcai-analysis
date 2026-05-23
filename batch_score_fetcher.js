/**
 * batch_score_fetcher.js
 *
 * 自动化脚本（分两步）：
 *   Step 1: node batch_score_fetcher.js --zyzcw
 *           从 zgzcw.com 批量获取所有无比分的比赛比分，写入Notion
 *   Step 2: 对于zgzcw未覆盖的比赛，由AI通过web_search补充
 *
 * 使用方式：
 *   node jingcai/batch_score_fetcher.js --zgzcw             # zgzcw批量获取并写入Notion
 *   node jingcai/batch_score_fetcher.js --zgzcw --date=2026-05-17  # 指定日期
 *   node jingcai/batch_score_fetcher.js --list-pending              # 列出所有无比分比赛
 *   node jingcai/batch_score_fetcher.js --web-update <input.json>  # 用web_search结果更新Notion
 *   node jingcai/batch_score_fetcher.js --dry-run --zgzcw          # 试运行不写入
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// ===== 配置 =====
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const PENDING_FILE = path.join(__dirname, '..', 'data', 'jingcai', 'pending_web_search.json');

// ===== 命令行参数 =====
const args = process.argv.slice(2);
const modeZgzcw = args.includes('--zgzcw');
const modeList = args.includes('--list-pending');
const modeWebUpdate = args.includes('--web-update') || args.some(a => a.startsWith('--web-update='));
const webUpdateFile = args.find(a => a.startsWith('--web-update='))?.split('=')[1];
const specificDate = args.find(a => a.startsWith('--date='))?.split('=')[1] || null;
const dryRun = args.includes('--dry-run');

// ===== Notion HTTP 封装 =====
function notion(method, p, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const opts = {
      hostname: 'api.notion.com',
      path: '/v1' + p,
      method,
      headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      }
    };
    if (data) opts.headers['Content-Length'] = Buffer.byteLength(data);
    const req = https.request(opts, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(d);
          if (res.statusCode >= 400) reject(new Error(`HTTP ${res.statusCode}: ${d.slice(0,200)}`));
          else resolve(parsed);
        } catch (e) {
          reject(new Error(`Parse error: ${d.slice(0,200)}`));
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

// ===== 获取所有 Notion 记录 =====
async function getAllPages() {
  console.log('[Notion] 查询数据库...');
  let all = [], cursor = null;
  while (true) {
    const body = { page_size: 100 };
    if (cursor) body.start_cursor = cursor;
    const r = await notion('POST', `/databases/${DB_ID}/query`, body);
    all = all.concat(r.results || []);
    cursor = r.next_cursor;
    if (!cursor) break;
  }
  console.log(`[Notion] 共 ${all.length} 条记录`);
  return all;
}

// ===== 从 Name/比赛 字段解析主客队 =====
// Notion数据库没有独立的 主队/客队 字段
// 比赛字段格式: "周一004 英超 阿森纳vs伯恩利" 或 "周一004 英超 阿森纳 vs 伯恩利"
function parseMatchFromName(nameStr, league) {
  if (!nameStr) return { home: '', away: '' };
  let rest = nameStr; // 周一004 英超 阿森纳vs伯恩利
  // 去掉 周XXX 编号
  rest = rest.replace(/^周[\u4e00-\u9fa5\d]+\s*/, '').trim();
  // 去掉联赛名（如果rest开头是联赛名）
  if (league && rest.startsWith(league)) {
    rest = rest.slice(league.length).trim();
  }
  // 用 vs 或 VS 或 VS 分割
  const sep = rest.match(/\s*v[ss]\s*|v[ss]/i);
  if (sep) {
    const before = rest.slice(0, sep.index);
    const after = rest.slice(sep.index + sep[0].length);
    return { home: before.trim(), away: after.trim() };
  }
  // 尝试中文方式
  if (rest.includes('vs')) {
    const parts = rest.split(/vs/i);
    if (parts.length === 2) return { home: parts[0].trim(), away: parts[1].trim() };
  }
  return { home: '', away: '' };
}

// ===== 提取比赛信息 =====
function extractMatch(page) {
  const p = page.properties;
  // Name 是标题字段
  const nameStr = (p['Name']?.title?.[0]?.plain_text || 
                   p['比赛']?.rich_text?.[0]?.plain_text || '').trim();
  // 竞彩编号：从Name前几个字提取
  const numMatch = nameStr.match(/^(周[\u4e00-\u9fa5\d]+)/);
  const matchNum = numMatch ? numMatch[1] : '';
  const dateRaw = p['比赛日期']?.date?.start || '';
  const date = dateRaw.replace(/T.*$/, '').trim();
  const league = p['联赛']?.select?.name || '';
  const { home, away } = parseMatchFromName(nameStr, league);
  const existingScore = (p['实际比分']?.rich_text?.[0]?.plain_text || '').trim();
  const existingResult = (p['实际结果']?.rich_text?.[0]?.plain_text || '').trim();
  const prediction = (p['竞彩预测']?.rich_text?.[0]?.plain_text || '').trim();
  return { pageId: page.id, matchNum, date, home, away, league,
    existingScore, existingResult, prediction };
}

// ===== 从 zgzcw 批量获取比分 =====
async function fetchZgzcw(dateStr) {
  return new Promise(resolve => {
    const url = `https://cp.zgzcw.com/lottery/jcplayvsForJsp.action?lotteryId=23&issue=${dateStr}`;
    https.get(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' },
      timeout: 15000
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const results = {};
        try {
          // 提取所有 tr mN="xxx"
          const rows = d.match(/<tr[^>]*?mN="([^"]*?)"[^>]*?>[\s\S]*?<\/tr>/g) || [];
          for (const row of rows) {
            const mNum = row.match(/mN="([^"]*)"/)?.[1];
            if (!mNum) continue;
            // 提取比分
            let score = row.match(/<td[^>]*?class="[^"]*?bf[^"]*?"[^>]*?>\s*(\d+):(\d+)\s*<\/td>/);
            if (!score) score = row.match(/<td class="wh-5 bf">\s*(\d+):(\d+)\s*<\/td>/);
            if (!score) score = row.match(/<span class="red"[^>]*?>\s*(\d+):(\d+)\s*<\/span>/);
            if (score) {
              const hs = parseInt(score[1]), as = parseInt(score[2]);
              if (hs <= 20 && as <= 20) results[mNum] = `${hs}:${as}`;
            }
          }
        } catch (e) { /* ignore parse error */ }
        resolve(results);
      });
    }).on('error', () => resolve({})).on('timeout', function() { this.destroy(); resolve({}); });
  });
}

// ===== 比分转结果 =====
function scoreResult(score) {
  if (!score || !score.includes(':')) return null;
  const p = score.split(':').map(Number);
  if (p.length !== 2 || isNaN(p[0]) || isNaN(p[1])) return null;
  return p[0] > p[1] ? '胜' : p[0] < p[1] ? '负' : '平';
}

function predResult(pred) {
  if (!pred) return null;
  if (pred.includes('主胜')) return '胜';
  if (pred.includes('客胜')) return '负';
  if (pred.includes('平局') || (pred.includes('平') && !pred.includes('负'))) return '平';
  return null;
}

// ===== 写入 Notion（单个） =====
async function updateScore(pageId, score, result, pred, rqPred) {
  const props = {
    '实际比分': { rich_text: [{ text: { content: score } }] },
    '实际结果': { rich_text: [{ text: { content: result } }] },
    '反馈日期': { date: { start: new Date().toISOString().split('T')[0] } },
  };

  if (pred) {
    const correct = predResult(pred) === result;
    props['预测正确'] = { checkbox: correct };
    props['反馈总结'] = {
      rich_text: [{
        text: {
          content: `竞彩预测: ${pred} → 实际: ${result} (${score}) ${correct ? '✅正确' : '❌错误'}`
        }
      }]
    };
  }

  return notion('PATCH', `/pages/${pageId}`, { properties: props });
}

// ===== 列出无比分的比赛 =====
async function listPending() {
  const pages = await getAllPages();
  let matches = pages.map(extractMatch).filter(m => !m.existingScore && m.matchNum);

  if (specificDate) matches = matches.filter(m => m.date === specificDate);

  console.log(`\n[待处理] 共 ${matches.length} 场无比分：\n`);

  const byDate = {};
  matches.forEach(m => (byDate[m.date] || (byDate[m.date] = [])).push(m));

  Object.entries(byDate).sort().forEach(([d, list]) => {
    console.log(`--- ${d} (${list.length} 场) ---`);
    list.forEach(m => console.log(`  ${m.matchNum} ${m.home} vs ${m.away} [${m.league}]`));
    console.log('');
  });

  // 保存到文件
  const dir = path.dirname(PENDING_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(PENDING_FILE, JSON.stringify(matches, null, 2), 'utf8');
  console.log(`[保存] 列表已保存到 ${PENDING_FILE}`);
}

// ===== zgzcw 批量获取并写入 =====
async function runZgzcwBatch() {
  const pages = await getAllPages();
  let matches = pages.map(extractMatch).filter(m => !m.existingScore && m.matchNum);

  if (specificDate) matches = matches.filter(m => m.date === specificDate);
  console.log(`\n[待处理] ${matches.length} 场无比分`);

  // 按日期分组
  const byDate = {};
  matches.forEach(m => (byDate[m.date] || (byDate[m.date] = [])).push(m));
  Object.entries(byDate).sort().forEach(([d, list]) => console.log(`  ${d}: ${list.length} 场`));

  if (matches.length === 0) { console.log('[完成] 所有比赛已有比分'); return; }

  // 逐日获取zgzcw
  const zgzcwMap = {}; // {date: {matchNum: score}}
  const dates = Object.keys(byDate).sort();
  for (const d of dates) {
    const r = await fetchZgzcw(d);
    zgzcwMap[d] = r;
  }

  // 统计
  let hit = 0, miss = 0, saved = 0, failed = 0;
  const missedMatches = [];

  for (const m of matches) {
    const scores = zgzcwMap[m.date] || {};
    const score = scores[m.matchNum];

    if (!score) {
      miss++;
      missedMatches.push(m);
      continue;
    }

    hit++;
    const result = scoreResult(score);
    if (!result) { console.log(`  ⚠️  ${m.matchNum} 比分异常: ${score}`); miss++; missedMatches.push(m); continue; }

    const pred = predResult(m.prediction);
    if (dryRun) {
      console.log(`  [DRY] ${m.matchNum} ${m.home} ${score} ${m.away} → ${result}` +
        (pred ? ` (预测:${pred})` : ''));
      continue;
    }

    try {
      await updateScore(m.pageId, score, result, pred);
      saved++;
      console.log(`  ✅ ${m.matchNum} ${m.home} ${score} ${m.away} → ${result}`);
    } catch (e) {
      console.log(`  ❌ ${m.matchNum} 写入失败: ${e.message.slice(0,80)}`);
      failed++;
    }
    await new Promise(r => setTimeout(r, 350));
  }

  console.log(`\n[结果] 命中 ${hit}/${matches.length}，写入 ${saved}，失败 ${failed}，未命中 ${miss}`);

  if (missedMatches.length > 0) {
    const dir = path.dirname(PENDING_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(PENDING_FILE, JSON.stringify(missedMatches, null, 2), 'utf8');
    console.log(`\n⚠️  ${missedMatches.length} 场未从zgzcw获取，已保存到 ${PENDING_FILE}`);
    console.log('   提示: AI agent 可用 web_search 逐场获取后调用 --web-update 写入');
  }
}

// ===== 用 web_search 结果更新 Notion =====
async function runWebUpdate(inputFile) {
  if (!inputFile) { console.error('[错误] --web-update 需要指定输入文件'); process.exit(1); }
  if (!fs.existsSync(inputFile)) { console.error('[错误] 文件不存在:', inputFile); process.exit(1); }

  const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  const matches = Array.isArray(data) ? data : [data];

  console.log(`[WebUpdate] 准备写入 ${matches.length} 场`);

  let saved = 0, failed = 0;
  for (const m of matches) {
    if (!m.score || !m.pageId) {
      console.log(`  ⚠️  缺少 score 或 pageId，跳过`);
      continue;
    }
    const result = scoreResult(m.score);
    if (!result) { console.log(`  ⚠️  ${m.matchNum || m.pageId} 比分无效: ${m.score}`); continue; }

    if (dryRun) {
      console.log(`  [DRY] ${m.matchNum} ${m.score} → ${result}`);
      continue;
    }

    try {
      await updateScore(m.pageId, m.score, result, m.prediction, m.rq_prediction);
      saved++;
      console.log(`  ✅ ${m.matchNum || m.pageId} ${m.score} → ${result}`);
    } catch (e) {
      console.log(`  ❌ ${m.matchNum || m.pageId} 写入失败: ${e.message.slice(0,80)}`);
      failed++;
    }
    await new Promise(r => setTimeout(r, 350));
  }

  console.log(`\n[完成] 写入 ${saved}，失败 ${failed}`);
}

// ===== 主入口 =====
(async () => {
  console.log('='.repeat(60));
  console.log('  batch_score_fetcher.js');
  console.log('  ' + new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
  console.log('='.repeat(60));

  if (modeList) {
    await listPending();
  } else if (modeZgzcw) {
    await runZgzcwBatch();
  } else if (modeWebUpdate) {
    await runWebUpdate(webUpdateFile);
  } else {
    console.log('\n用法:');
    console.log('  --list-pending              列出所有无比分比赛');
    console.log('  --zgzcw                     从zgzcw获取比分并写入Notion');
    console.log('  --zgzcw --date=2026-05-17   指定日期');
    console.log('  --zgzcw --dry-run           试运行');
    console.log('  --web-update=<file.json>    用web_search结果更新Notion');
    console.log('');
    // 默认行为：列出
    await listPending();
  }
})().catch(e => { console.error('[FATAL]', e); process.exit(1); });
