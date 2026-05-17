// 竞彩数据同步到Notion 数据库 V3 - 合并比赛列 + 修复数据提取
const https = require('https');
const fs = require('fs');
const path = require('path');

const NOTION_API_KEY = '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';
const DATABASE_ID = '93490bfb-ac43-49be-a24d-9e3e5a225991';
const JINGCAI_DIR = path.join(__dirname);
const TASKS_DIR = path.join(JINGCAI_DIR, 'tasks');

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
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

function extractMatchInfo(reportPath) {
  const content = fs.readFileSync(reportPath, 'utf8');
  const fn = path.basename(reportPath);
  
  // 提取竞彩编号
  const mn = fn.match(/周[一二三四五六日](\d{3})/);
  const matchNum = mn ? mn[1] : '';
  const dayPrefix = mn ? fn.match(/周[一二三四五六日]/)[0] : '';
  
  // 提取对阵
  const tm = fn.match(/周[一二三四五六日]\d{3}_(.+?)vs(.+?)\.md/);
  const home = tm ? tm[1].trim() : '';
  const away = tm ? tm[2].trim() : '';
  
  // 提取联赛
  let league = '';
  const lm = content.match(/比赛[：:]\s*([^·\n]+)·/);
  if (lm) league = lm[1].trim();
  
  // 构建"比赛"列：周X0XX 联赛 主队vs客队
  const matchDisplay = `${dayPrefix}${matchNum} ${league} ${home}vs${away}`.trim();
  
  // 提取推荐
  let pred = '';
  const rec = content.match(/\*\*推荐\*\*\s*\|\s*([^\|]+)/);
  if (rec) pred = rec[1].trim();
  
  // 提取信心
  let conf = '';
  const cm = content.match(/\*\*信心\*\*\s*\|\s*([^\|]+)/);
  if (cm) conf = cm[1].trim();
  // 提取信心等级
  const confLevel = conf.match(/([^\(（]+)/);
  const confLevelText = confLevel ? confLevel[1].trim() : '';
  
  // 提取盘路匹配（第七部分 - 任意公司盘路匹配汇总）
  let panlu = '';
  const pm = content.match(/任意公司盘路匹配汇总\s*\(\s*(\d+)\s*场\)/);
  if (pm) panlu = pm[1] + ' 场';
  
  // 提取欧赔趋势
  let oupei = '';
  const om = content.match(/欧赔趋势[:\s]+([^（\n]+)/);
  if (om) oupei = om[1].trim();
  if (!oupei) {
    const om2 = content.match(/欧赔趋势: ([^\n]+)/);
    if (om2) oupei = om2[1].trim();
  }
  
  // 提取让球趋势 - 从让球基础信息提取
  let rangqiu = '';
  const rq2 = content.match(/竞彩让球(?:初盘|终盘)[：:]\s*([\d.]+)\s*\/\s*([\d.]+)\s*\/\s*([\d.]+)/);
  if (rq2) rangqiu = `初:${rq2[1]}/${rq2[2]}/${rq2[3]}`;
  if (!rangqiu) {
    const rq3 = content.match(/让球\s*\|\s*初盘胜.*?\n[\s\S]*?\n.*?\n[\s\S]*?\|\s*([\w\u4e00-\u9fff]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/);
    if (rq3) rangqiu = `${rq3[1]} 初:${rq3[2]}/${rq3[3]}/${rq3[4]}`;
  }
  
  // 提取亚盘趋势 - 澳门亚盘
  let yapan = '';
  const ym = content.match(/澳门亚盘[:\s]+([^\n]{2,30})/);
  if (ym) yapan = ym[1].trim();
  
  // 提取百家对比
  let baijia = '';
  const bm = content.match(/百家平均欧赔[:\s]+([^\n]{2,50})/);
  if (bm) baijia = bm[1].trim();
  
  return {
    matchDisplay, matchNum, home, away, league, pred, conf: confLevelText,
    panlu, oupei, rangqiu, yapan, baijia,
  };
}

async function addMatch(dateStr, info) {
  const props = {
    '竞彩编号': notionRichTextProp(info.matchNum),
    '比赛日期': { date: { start: dateStr } },
    '联赛': notionRichTextProp(info.league),
    '主队': notionRichTextProp(info.home),
    '客队': notionRichTextProp(info.away),
    '竞彩预测': notionRichTextProp(info.pred),
    '竞彩信心': notionSelectProp(info.conf),
    '最终报告': notionRichTextProp(info.matchDisplay), // 用比赛列填充
    '盘路匹配': notionRichTextProp(info.panlu),
    '欧赔趋势': notionRichTextProp(info.oupei),
    '让球趋势': notionRichTextProp(info.rangqiu),
    '亚盘趋势': notionRichTextProp(info.yapan),
    '百家对比': notionRichTextProp(info.baijia),
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
    return f.match(/周[一二三四五六日]\d{3}_/);
  });
  
  console.log(`[INFO] 找到 ${files.length} 份报告`);
  
  let successCount = 0;
  for (const f of files) {
    const info = extractMatchInfo(path.join(taskDir, f));
    const pageId = await addMatch(dateStr, info);
    if (pageId) successCount++;
    await new Promise(r => setTimeout(r, 300));
  }
  
  console.log(`[DONE] 成功 ${successCount}/${files.length}`);
}

const cmd = process.argv[2];
const dateStr = process.argv[3];

if (cmd === 'add' && dateStr) {
  syncDate(dateStr);
} else {
  console.log('用法: node sync_notion_v3.js add <date>');
}
