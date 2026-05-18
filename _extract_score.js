/**
 * 从 step9/step14 历史交手记录中提取本场比赛的实际比分和赛果
 * 用法: node _extract_score.js <date> [date2 ...]
 * 示例: node _extract_score.js 2026-05-01 2026-05-02 2026-05-03 2026-05-04 2026-05-05 2026-05-06
 */
const fs = require('fs');
const path = require('path');

const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
const NOTION_DB = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const API_KEY = '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';

const dates = process.argv.slice(2);
if (dates.length === 0) {
  console.log('用法: node _extract_score.js 2026-05-01 [2026-05-02 ...]');
  process.exit(1);
}

const https = require('https');

async function fetchMatchFromNotion(date, matchNum) {
  // 从Notion查询比赛记录获取 page id
  return new Promise((resolve, reject) => {
    const query = {
      filter: {
        and: [
          { property: '比赛日期', date: { equals: date } },
          { property: 'Name', title: { contains: matchNum } }
        ]
      },
      page_size: 1
    };
    const qs = JSON.stringify(query);
    const req = https.request({
      hostname: 'api.notion.com',
      path: '/v1/databases/' + NOTION_DB + '/query',
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(qs)
      }
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const r = JSON.parse(d);
        if (r.results && r.results.length > 0) {
          resolve(r.results[0]);
        } else {
          resolve(null);
        }
      });
    });
    req.on('error', reject);
    req.write(qs);
    req.end();
  });
}

async function updateNotionScore(pageId, score, result) {
  return new Promise((resolve, reject) => {
    const props = {
      '实际比分': { rich_text: [{ text: { content: score } }] },
      '实际结果': { rich_text: [{ text: { content: result } }] },
      '反馈日期': { date: { start: new Date().toISOString().split('T')[0] } }
    };
    const data = JSON.stringify({ properties: props });
    const req = https.request({
      hostname: 'api.notion.com',
      path: '/v1/pages/' + pageId,
      method: 'PATCH',
      headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        if (res.statusCode >= 400) reject(new Error('HTTP ' + res.statusCode));
        else resolve();
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function extractScore(date) {
  const taskDir = path.join(BASE, date, 'data');
  if (!fs.existsSync(taskDir)) {
    console.log('[' + date + '] 数据目录不存在: ' + taskDir);
    return { total: 0, found: 0 };
  }

  const matchDirs = fs.readdirSync(taskDir).filter(d => d.startsWith('match'));
  let total = matchDirs.length;
  let found = 0;

  for (const matchDir of matchDirs) {
    const matchPath = path.join(taskDir, matchDir);

    // 读取 meta.json 获取比赛信息
    const metaPath = path.join(matchPath, 'meta.json');
    if (!fs.existsSync(metaPath)) continue;
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    const matchNum = meta.matchnum || '';
    const home = meta.home || '';
    const away = meta.away || '';

    // 尝试从 step9 和 step14 提取比分
    const teamA = path.join(matchPath, 'group04_teamA', 'step9_home_history.txt');
    const teamB = path.join(matchPath, 'group05_teamB', 'step14_away_history.txt');

    let score = '';
    let halfScore = '';
    let result = '';

    // 从 step9 中找
    if (fs.existsSync(teamA)) {
      const data = fs.readFileSync(teamA, 'utf8');
      // 第一个表格的行格式: | 序号 | 日期 | 对阵 | 比分 | 半场 | 赛果 | 盘口 | 盘路 | 大小 |
      const lines = data.split('\n');
      for (const line of lines) {
        if (line.startsWith('|') && line.includes(' vs ')) {
          const cols = line.split('|').map(c => c.trim());
          // 格式: | 序号 | 日期 | 对阵 | 比分 | 半场 | 赛果 | ...
          if (cols.length >= 7) {
            const matchName = cols[3]; // 对阵列
            // 检查是否匹配本场比赛
            if (matchName.includes(home) || matchName.includes(away)) {
              const s = cols[4]; // 比分列
              const r = cols[6]; // 赛果列
              // 比分格式: 3:0 或 0:0
              if (s.match(/^\d+:\d+$/)) {
                score = s;
                result = r;
                halfScore = cols[5] || '';
                break;
              }
            }
          }
        }
      }
    }

    // 如果 step9 没找到，尝试 step14
    if (!score && fs.existsSync(teamB)) {
      const data = fs.readFileSync(teamB, 'utf8');
      const lines = data.split('\n');
      for (const line of lines) {
        if (line.startsWith('|') && line.includes(' vs ')) {
          const cols = line.split('|').map(c => c.trim());
          if (cols.length >= 7) {
            const matchName = cols[3];
            if (matchName.includes(home) || matchName.includes(away)) {
              const s = cols[4];
              const r = cols[6];
              if (s.match(/^\d+:\d+$/)) {
                score = s;
                result = r;
                break;
              }
            }
          }
        }
      }
    }

    if (score) {
      found++;
      const matchInfo = matchNum + ' ' + home + ' vs ' + away;
      console.log('  [OK] ' + matchInfo + ' -> ' + score + ' (' + result + ')');

      // 更新到 Notion
      const matchName = matchNum + ' ' + meta.league + ' ' + home + 'vs' + away;
      try {
        const page = await fetchMatchFromNotion(date, matchNum);
        if (page) {
          // 检查是否已有比分
          const existingScore = page.properties['实际比分']?.rich_text?.[0]?.plain_text;
          if (!existingScore) {
            await updateNotionScore(page.id, score, result);
            console.log('    -> 已写入Notion');
          } else {
            console.log('    -> 已有比分: ' + existingScore + '，跳过');
          }
        } else {
          console.log('    -> Notion未找到对应页面');
        }
      } catch (e) {
        console.log('    -> Notion更新失败: ' + e.message);
      }
    } else {
      console.log('  [--] ' + matchNum + ' ' + home + ' vs ' + away + ' -> 未找到比分');
    }
  }

  return { total, found };
}

(async () => {
  let grandTotal = 0;
  let grandFound = 0;

  for (const date of dates) {
    console.log('\n=== ' + date + ' ===');
    const r = await extractScore(date);
    grandTotal += r.total;
    grandFound += r.found;
    console.log('  -> ' + r.found + '/' + r.total + ' 场有比分');
  }

  console.log('\n========================================');
  console.log('总计: ' + grandFound + '/' + grandTotal + ' 场找到了比分');
  console.log('========================================');
})();
