// Add step columns to Notion database, then sync test report
const https = require('https');
const fs = require('fs');
const path = require('path');

const NOTION_API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body || ''),
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
    if (body) req.write(body);
    req.end();
  });
}

// Step 1: Update database schema - add all needed properties
async function updateDatabaseSchema() {
  console.log('=== Step 1: Update Database Schema ===');
  
  // Build properties update payload
  const properties = {};
  
  // Add standard meta fields
  properties['联赛'] = { select: {} };
  properties['主队'] = { rich_text: {} };
  properties['客队'] = { rich_text: {} };
  properties['比赛时间'] = { date: {} };
  properties['让球'] = { rich_text: {} };
  properties['澳门亚盘'] = { rich_text: {} };
  properties['竞彩预测'] = { rich_text: {} };
  properties['竞彩信心'] = { rich_text: {} };
  
  // Add 26 step columns
  for (let i = 1; i <= 26; i++) {
    properties[`第${i}步`] = { rich_text: {} };
  }
  
  // Final conclusion
  properties['最终结论'] = { rich_text: {} };
  
  const r = await notionRequest('PATCH', `/v1/databases/${DB_ID}`, { properties });
  console.log('Status:', r.status);
  if (r.status === 200) {
    console.log('Schema updated successfully!');
    console.log('Properties:', Object.keys(r.data.properties).length);
  } else {
    console.log('Error:', JSON.stringify(r.data, null, 2).substring(0, 500));
  }
  return r;
}

// Step 2: Parse report
function parseReport(content) {
  const steps = {};
  const meta = {};

  // Extract meta
  const m = (re) => { const x = content.match(re); return x ? x[1].trim() : ''; };
  
  // Title parsing: 周三005_布雷斯特vs斯特拉斯
  const tm = content.match(/# 周([^\d]+\d+)_\s*(.+?)vs(.+)/);
  if (tm) {
    meta.竞彩编号 = '周' + tm[1];
    meta.主队 = tm[2].trim();
    meta.客队 = tm[3].replace(/\s*#.*/, '').trim();
  }
  
  meta.联赛 = m(/比赛[::]\s*([^·\n]+)·/);
  meta.比赛时间 = m(/比赛时间:\s*(.+)$/m);
  meta.让球 = m(/让球:\s*(.+)$/m);
  meta.澳门亚盘 = m(/澳门亚盘:\s*(.+)$/m);
  
  // Extract from conclusion table
  const predMatch = content.match(/\*\*竞彩预测\*\*\s*\|\s*(.+?)(?=\n|$)/);
  if (predMatch) meta.竞彩预测 = predMatch[1].trim();
  
  const confMatch = content.match(/\*\*信心\*\*\s*\|\s*(.+?)(?=\n|$)/);
  if (confMatch) meta.竞彩信心 = confMatch[1].trim();

  // Parse steps
  // Step 1-8
  for (let i = 1; i <= 8; i++) {
    const h = `## 第${i}步`;
    const nh = i < 8 ? `## 第${i+1}步` : '# 第四部分';
    const si = content.indexOf(h);
    if (si >= 0) {
      const ni = content.indexOf(nh, si + h.length);
      steps[`第${i}步`] = content.substring(si, ni >= 0 ? ni : content.length).trim();
    }
  }

  // Step 9: 第四部分 -> 第十步
  const s9s = content.indexOf('# 第四部分');
  const s10s = content.indexOf('## 第十步');
  if (s9s >= 0 && s10s >= 0) steps['第9步'] = content.substring(s9s, s10s).trim();

  // Step 10-18
  const cn = ['十','十一','十二','十三','十四','十五','十六','十七','十八','十九','二十','二十一','二十二','二十三','二十四','二十五','二十六'];
  for (let i = 10; i <= 18; i++) {
    const idx = i - 10;
    const h = `## 第${cn[idx]}步`;
    // Step 14 has no explicit heading, so step 13's next is step 15
    let nh;
    if (i === 13) {
      nh = '## 第十五步';
    } else if (i < 18) {
      nh = `## 第${cn[idx+1]}步`;
    } else {
      nh = '# 第六部分';
    }
    const si = content.indexOf(h);
    if (si >= 0) {
      const ni = content.indexOf(nh, si + h.length);
      steps[`第${i}步`] = content.substring(si, ni >= 0 ? ni : content.length).trim();
    }
  }
  // Step 14 has no explicit heading, use section content
  const s14s = content.indexOf('# 第五部分');
  const s15s = content.indexOf('## 第十五步');
  if (s14s >= 0 && s15s >= 0) steps['第14步'] = content.substring(s14s, s15s).trim();

  // Step 19: 第六部分 -> 第二十步
  const s19s = content.indexOf('# 第六部分');
  const s20s = content.indexOf('## 第二十步');
  if (s19s >= 0 && s20s >= 0) steps['第19步'] = content.substring(s19s, s20s).trim();

  // Step 20-21
  for (let i = 20; i <= 21; i++) {
    const h = `## 第${cn[i-10]}步`;
    const nh = `## 第${cn[i-10+1]}步`;
    const si = content.indexOf(h);
    if (si >= 0) {
      const ni = content.indexOf(nh, si + h.length);
      steps[`第${i}步`] = content.substring(si, ni >= 0 ? ni : content.length).trim();
    }
  }

  // Step 22: between 21 and 23
  const s21s = content.indexOf('## 第二十一步');
  const s23s = content.indexOf('## 第二十三步');
  if (s21s >= 0 && s23s >= 0) steps['第22步'] = content.substring(s21s, s23s).trim();

  // Step 23: 第二十三步 -> 第七部分
  if (s23s >= 0) {
    const ni = content.indexOf('# 第七部分', s23s);
    steps['第23步'] = content.substring(s23s, ni >= 0 ? ni : content.length).trim();
  }

  // Step 24: 第七部分 -> 第八部分:
  const s24s = content.indexOf('# 第七部分');
  const s25s = content.indexOf('# 第八部分:');
  if (s24s >= 0 && s25s >= 0) steps['第24步'] = content.substring(s24s, s25s).trim();

  // Step 25: 第八部分: 庄家盈亏分析
  const s25h = '# 第八部分: 庄家盈亏分析';
  const s26h = '# 第八部分续: 庄家盈亏占比分析';
  const s25i = content.indexOf(s25h);
  const s26i = content.indexOf(s26h);
  if (s25i >= 0 && s26i >= 0) steps['第25步'] = content.substring(s25i, s26i).trim();

  // Step 26
  const s27s = content.indexOf('# 第九部分');
  if (s26i >= 0 && s27s >= 0) steps['第26步'] = content.substring(s26i, s27s).trim();

  // Final conclusion
  if (s27s >= 0) {
    let c = content.substring(s27s).trim();
    c = c.replace(/\n---+[\s\S]*$/, '');
    steps['最终结论'] = c;
  }

  return { steps, meta };
}

function notionTitle(text) {
  return { title: [{ text: { content: String(text) } }] };
}

function notionRichText(text) {
  if (!text) return { rich_text: [] };
  const chunks = [];
  const max = 1900;
  for (let i = 0; i < text.length; i += max) {
    chunks.push({ text: { content: text.substring(i, i + max) } });
  }
  return { rich_text: chunks };
}

function notionSelect(value) {
  return value ? { select: { name: String(value) } } : { select: null };
}

function notionDate(value) {
  return value ? { date: { start: value } } : { date: null };
}

// Main
(async () => {
  // Step 1: Update schema
  await updateDatabaseSchema();
  
  // Step 2: Parse report
  const reportPath = path.join(__dirname, 'tasks', '2026-05-13', '周三005_布雷斯特vs斯特拉斯.md');
  const content = fs.readFileSync(reportPath, 'utf8');
  const { steps, meta } = parseReport(content);
  
  console.log('\n=== Parsed Steps ===');
  for (let i = 1; i <= 26; i++) {
    const l = `第${i}步`;
    console.log(`  ${l}: ${steps[l] ? steps[l].length : 0} chars`);
  }
  console.log(`  最终结论: ${steps['最终结论'] ? steps['最终结论'].length : 0} chars`);
  console.log('\n=== Meta ===', meta);

  // Step 3: Create page
  console.log('\n=== Step 3: Create Page ===');
  const title = `${meta.竞彩编号} ${meta.主队}vs${meta.客队}`;
  const properties = { '比赛': notionTitle(title) };
  
  if (meta.联赛) properties['联赛'] = notionSelect(meta.联赛);
  if (meta.主队) properties['主队'] = notionRichText(meta.主队);
  if (meta.客队) properties['客队'] = notionRichText(meta.客队);
  if (meta.竞彩预测) properties['竞彩预测'] = notionRichText(meta.竞彩预测);
  if (meta.竞彩信心) properties['竞彩信心'] = notionRichText(meta.竞彩信心);
  if (meta.比赛时间) properties['比赛时间'] = notionDate(meta.比赛时间);
  if (meta.让球) properties['让球'] = notionRichText(meta.让球);
  if (meta.澳门亚盘) properties['澳门亚盘'] = notionRichText(meta.澳门亚盘);
  
  for (let i = 1; i <= 26; i++) {
    properties[`第${i}步`] = notionRichText(steps[`第${i}步`] || '');
  }
  properties['最终结论'] = notionRichText(steps['最终结论'] || '');
  
  const r = await notionRequest('POST', '/v1/pages', {
    parent: { database_id: DB_ID },
    properties,
  });
  
  console.log('Status:', r.status);
  if (r.status === 200) {
    console.log('Page created:', r.data.id);
    console.log('SUCCESS!');
  } else {
    console.log('Error:', JSON.stringify(r.data, null, 2).substring(0, 800));
  }
})();
