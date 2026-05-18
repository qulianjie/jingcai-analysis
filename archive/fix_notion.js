// 修复05-01到05-05的Notion记录：删除无效行 + 重新同步
const https = require('https');
const fs = require('fs');
const path = require('path');

const NOTION_API_KEY = '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';
const DATABASE_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const TASKS_DIR = path.join(__dirname, 'tasks');

const headers = {
  'Authorization': 'Bearer ' + NOTION_API_KEY,
  'Notion-Version': '2022-06-28',
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

// 删除一条记录
async function deletePage(pageId) {
  const res = await notionRequest('PATCH', `/v1/pages/${pageId}`, { archived: true });
  return res.status === 200;
}

// 查询某天的所有记录
async function queryByDate(dateStr) {
  const data = JSON.stringify({
    filter: {
      property: '比赛日期',
      date: { equals: dateStr },
    },
    page_size: 100,
  });
  const res = await notionRequest('POST', '/v1/databases/' + DATABASE_ID + '/query', JSON.parse(data));
  return res.data?.results || [];
}

// 从本地报告文件提取比赛信息
function extractFromReport(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const fn = path.basename(filePath);
  
  // 提取周x0xx
  const mn = fn.match(/周([一二三四五六日])(\d{3})/);
  const dayPrefix = mn ? '周' + mn[1] + mn[2] : '';
  
  // 提取联赛
  let league = '';
  const lm = content.match(/比赛[::]\s*([^·\n]+)·/);
  if (lm) league = lm[1].trim();
  
  // 提取对阵
  const tm = fn.match(/周[一二三四五六日]\d{3}_(.+?)vs(.+?)\.md/);
  const home = tm ? tm[1].trim() : '';
  const away = tm ? tm[2].trim() : '';
  
  return { dayPrefix, league, home, away, matchDisplay: `${dayPrefix} ${league} ${home}vs${away}` };
}

// 更新一条记录的比赛字段
async function updateMatch(pageId, matchDisplay) {
  const props = {
    'Name': { title: [{ text: { content: matchDisplay } }] },
    '比赛': { rich_text: [{ text: { content: matchDisplay } }] },
  };
  const res = await notionRequest('PATCH', `/v1/pages/${pageId}`, { properties: props });
  return res.status === 200;
}

async function main() {
  const dates = ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05'];
  let totalDeleted = 0;
  let totalUpdated = 0;
  
  for (const dateStr of dates) {
    console.log(`\n=== ${dateStr} ===`);
    
    // 查询Notion中的记录
    const notionRecords = await queryByDate(dateStr);
    console.log(`Notion记录数: ${notionRecords.length}`);
    
    // 读取本地报告文件
    const taskDir = path.join(TASKS_DIR, dateStr);
    if (!fs.existsSync(taskDir)) {
      console.log(`  本地目录不存在，跳过`);
      continue;
    }
    
    const reportFiles = fs.readdirSync(taskDir).filter(f => f.endsWith('.md'));
    console.log(`本地报告数: ${reportFiles.length}`);
    
    // 建立编号映射
    const localMap = {};
    for (const rf of reportFiles) {
      const info = extractFromReport(path.join(taskDir, rf));
      const numMatch = info.dayPrefix.match(/(\d{3})/);
      if (numMatch) {
        localMap[numMatch[1]] = info;
      }
    }
    
    // 处理Notion记录
    for (const record of notionRecords) {
      const pageId = record.id;
      const notionName = record.properties['Name']?.title?.[0]?.plain_text || '';
      const notionMatch = record.properties['比赛']?.rich_text?.[0]?.plain_text || '';
      
      // 提取编号
      const numMatch = notionName.match(/(\d{3})/);
      const num = numMatch ? numMatch[1] : '';
      
      if (num && localMap[num]) {
        // 有对应本地文件 → 更新
        const localInfo = localMap[num];
        const success = await updateMatch(pageId, localInfo.matchDisplay);
        if (success) {
          console.log(`  ✅ 更新 ${num}: ${notionName} → ${localInfo.matchDisplay}`);
          totalUpdated++;
        } else {
          console.log(`  ❌ 更新失败 ${num}`);
        }
      } else if (notionName.length < 10) {
        // 没有对应本地文件且名称很短 → 删除
        const success = await deletePage(pageId);
        if (success) {
          console.log(`  🗑️ 删除 ${notionName}`);
          totalDeleted++;
        } else {
          console.log(`  ❌ 删除失败 ${notionName}`);
        }
      }
    }
  }
  
  console.log(`\n=== 完成 ===`);
  console.log(`删除: ${totalDeleted} 条`);
  console.log(`更新: ${totalUpdated} 条`);
}

main().catch(console.error);
