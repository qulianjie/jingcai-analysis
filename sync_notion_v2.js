// 竞彩数据同步到Notion 数据库 V2
// 用法:
//   node sync_notion_v2.js add <date>          # 添加比赛（从流水线报告提取）
//   node sync_notion_v2.js update <date>       # 更新反馈（从赛果提取）

const https = require('https');
const fs = require('fs');
const path = require('path');

const NOTION_API_KEY = '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';
const DATABASE_ID = 'aa554c81-1ff8-497c-88b1-c04eecc383ff';
const JINGCAI_DIR = path.join(__dirname);
const TASKS_DIR = path.join(JINGCAI_DIR, 'tasks');

const headers = {
  'Authorization': 'Bearer ' + NOTION_API_KEY,
  'Notion-Version': '2025-09-03',
  'Content-Type': 'application/json',
};

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        ...headers,
        'Content-Length': Buffer.byteLength(body || ''),
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(d) });
        } catch (e) {
          resolve({ status: res.statusCode, data: d });
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function notionRichTextProp(text) {
  return text ? { rich_text: [{ text: { content: String(text) } }] } : { rich_text: [] };
}

function notionSelectProp(value) {
  return value ? { select: { name: String(value) } } : { select: null };
}

function notionDateProp(dateStr) {
  return dateStr ? { date: { start: dateStr } } : { date: null };
}

function notionCheckboxProp(value) {
  return { checkbox: Boolean(value) };
}

function extractMatchInfo(reportPath) {
  const content = fs.readFileSync(reportPath, 'utf8');
  const fn = path.basename(reportPath);
  
  // 提取竞彩编号 (e.g. 周六001 → 001)
  const mn = fn.match(/周[一二三四五六日](\d{3})/);
  const matchNum = mn ? mn[1] : '';
  
  // 提取对阵 (e.g. 周六001_奥克兰FCvs墨尔本城.md)
  const tm = fn.match(/周[一二三四五六日]\d{3}_(.+?)vs(.+?)\.md/);
  const home = tm ? tm[1].trim() : '';
  const away = tm ? tm[2].trim() : '';
  
  // 提取联赛
  let league = '';
  const lm = content.match(/比赛[：:]\s*([^·\n]+)·/);
  if (lm) league = lm[1].trim();
  
  // 提取推荐（胜平负）
  let pred = '';
  const rec = content.match(/\*\*推荐\*\*\s*\|\s*([^\|]+)/);
  if (rec) pred = rec[1].trim();
  
  // 提取让球预测
  let rqPred = '';
  const rqRec = content.match(/\*\*让球预测\*\*\s*\|\s*([^\|]+)/);
  if (rqRec) rqPred = rqRec[1].trim();
  
  // 提取信心
  let conf = '';
  const cm = content.match(/\*\*信心\*\*\s*\|\s*([^\|]+)/);
  if (cm) conf = cm[1].trim();
  
  // 提取综合分值
  let score = '';
  const sm = content.match(/\*\*综合分值\*\*\s*\|\s*([^\|]+)/);
  if (sm) score = sm[1].trim();
  
  // 提取数据质量
  let quality = '';
  const qm = content.match(/\*\*数据质量\*\*\s*\|\s*([^\|]+)/);
  if (qm) quality = qm[1].trim();
  
  // 提取盘路匹配（从第七部分）
  let panlu = '';
  const pm = content.match(/## 第七部分: 盘路完全匹配汇总.*?任意公司盘路匹配汇总 \((\d+) 场\)/s);
  if (pm) panlu = pm[1] + ' 场匹配';
  
  // 提取欧赔趋势 - 从第1步提取
  let oupei = '';
  const om = content.match(/## 第1步: 欧盘基础信息.*?竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/s);
  if (om) oupei = `初:${om[1]}/${om[2]}/${om[3]} → 终:${om[4]}/${om[5]}/${om[6]}`;
  
  // 提取让球趋势 - 从第4步提取
  let rangqiu = '';
  const rm = content.match(/## 第4步: 让球指数基础信息.*?竞彩足球.*?让球基础信息[\s\S]*?让球\s*\|\s*初盘胜\s*\|\s*初盘平\s*\|\s*初盘负[\s\S]*?([\d.-]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/s);
  if (rm) rangqiu = `让球:${rm[1]} 初:${rm[2]}/${rm[3]}/${rm[4]}`;
  
  // 提取亚盘趋势 - 从第6步提取
  let yapan = '';
  const ym = content.match(/## 第6步: 亚盘对比基础信息[\s\S]*?澳门亚盘[:\s]*([^\n]+)/);
  if (ym) yapan = ym[1].trim();
  if (!yapan) {
    const ym2 = content.match(/澳门亚盘[:\s]*([^\n]+)/);
    if (ym2) yapan = ym2[1].trim();
  }
  
  // 提取百家对比 - 从第六部分提取
  let baijia = '';
  const bm = content.match(/## 第六部分: 百家对比分析[\s\S]*?百家平均欧赔[:\s]*([^\n]+)/);
  if (bm) baijia = bm[1].trim();
  
  // 构建"比赛"列：周X0XX 联赛 主队vs客队
  const matchDisplay = `${mn ? mn[0] : ''} ${league} ${home}vs${away}`.trim();
  
  return {
    matchDisplay,
    matchNum, home, away, league, pred, rqPred, conf, score, quality,
    panlu, oupei, rangqiu, yapan, baijia,
  };
}

async function addMatch(dateStr, info) {
  const props = {
    '比赛': notionRichTextProp(info.matchDisplay),
    '竞彩编号': notionRichTextProp(info.matchNum),
    '联赛': notionRichTextProp(info.league),
    '主队': notionRichTextProp(info.home),
    '客队': notionRichTextProp(info.away),
    '竞彩预测': notionRichTextProp(info.pred),
    '让球预测': notionRichTextProp(info.rqPred),
    '竞彩信心': notionSelectProp(info.conf),
    '盘路匹配': notionRichTextProp(info.panlu),
    '欧赔趋势': notionRichTextProp(info.oupei),
    '让球趋势': notionRichTextProp(info.rangqiu),
    '亚盘趋势': notionRichTextProp(info.yapan),
    '百家对比': notionRichTextProp(info.baijia),
    '综合分值': notionRichTextProp(info.score),
    '数据质量': notionRichTextProp(info.quality),
  };
  
  const res = await notionRequest('POST', '/v1/pages', {
    parent: { database_id: DATABASE_ID },
    properties: props,
  });
  
  if (res.status === 200) {
    console.log(`[OK] ${info.matchDisplay}`);
    return res.data.id;
  } else {
    console.error(`[ERR] ${info.matchDisplay}: ${res.status} ${JSON.stringify(res.data).substring(0, 200)}`);
    return null;
  }
}

async function syncDate(dateStr) {
  const taskDir = path.join(TASKS_DIR, dateStr);
  if (!fs.existsSync(taskDir)) {
    console.log(`[WARN] 没有找到 ${dateStr} 的报告`);
    return;
  }
  
  const files = fs.readdirSync(taskDir).filter(f => {
    if (!f.endsWith('.md')) return false;
    // 跳过 sunday_matches.md 等元数据文件
    return f.match(/周[一二三四五六日]\d{3}_/);
  });
  
  console.log(`[INFO] 找到 ${files.length} 份报告`);
  
  let successCount = 0;
  for (const f of files) {
    const info = extractMatchInfo(path.join(taskDir, f));
    const pageId = await addMatch(dateStr, info);
    if (pageId) successCount++;
    await new Promise(r => setTimeout(r, 300)); // 避免限流
  }
  
  console.log(`[DONE] 成功 ${successCount}/${files.length}`);
}

// ===== Main =====
const cmd = process.argv[2];
const dateStr = process.argv[3];

if (cmd === 'add' && dateStr) {
  syncDate(dateStr);
} else {
  console.log('用法:');
  console.log('  node sync_notion_v2.js add <date>    # 添加比赛');
  console.log('  node sync_notion_v2.js update <date> # 更新反馈');
}
