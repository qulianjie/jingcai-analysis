// 从500.com抓取终盘欧赔，更新到Notion
// 用法: node fetch_final_odds.js

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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

// 从500.com抓取欧赔数据
function fetchOddsFrom500(fid) {
  return new Promise((resolve, reject) => {
    const url = `https://odds.500.com/fenxi/ouzhi-${fid}.shtml`;
    const options = {
      hostname: 'odds.500.com',
      path: `/fenxi/ouzhi-${fid}.shtml`,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
      },
      timeout: 15000,
    };

    const req = https.request(options, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          // 用GBK解码
          const iconv = require('iconv-lite');
          const text = iconv.decode(Buffer.from(data, 'binary'), 'gbk');
          resolve(parseOddsTable(text));
        } catch (e) {
          resolve(null);
        }
      });
    });
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
    req.end();
  });
}

// 解析欧赔表格
function parseOddsTable(html) {
  const result = {};
  
  // 匹配公司行: | 1 | 竞彩官方 | x.x | x.x | x.x | x.x | x.x | x.x | ... |
  const companyRegex = /\|\s*(\d+)\s*\|\s*([^|]+)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|/g;
  let match;
  
  while ((match = companyRegex.exec(html)) !== null) {
    const rowNum = parseInt(match[1].trim());
    const name = match[2].trim();
    
    // 提取6个赔率值: 初胜、初平、初负、即胜、即平、即负
    const nums = [];
    for (let i = 3; i <= 8; i++) {
      const val = match[i].trim().replace(/\s/g, '');
      const num = parseFloat(val);
      if (!isNaN(num)) nums.push(num);
    }
    
    if (nums.length >= 6) {
      if (rowNum === 1 || name === '竞彩官方') {
        // 竞彩: 即时胜/平/负 (索引3,4,5)
        result.jc = {
          win: Math.floor(nums[3] * 10) / 10,
          draw: Math.floor(nums[4] * 10) / 10,
          loss: Math.floor(nums[5] * 10) / 10,
        };
      }
      if (rowNum === 6 || name === 'Interwetten') {
        result.iw = {
          win: Math.floor(nums[3] * 10) / 10,
          draw: Math.floor(nums[4] * 10) / 10,
          loss: Math.floor(nums[5] * 10) / 10,
        };
      }
      if (name.includes('平均值') || name.includes('平均')) {
        result.bj = {
          win: Math.floor(nums[3] * 10) / 10,
          draw: Math.floor(nums[4] * 10) / 10,
          loss: Math.floor(nums[5] * 10) / 10,
        };
      }
    }
  }
  
  return result;
}

// 查询Notion记录
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

// 更新Notion记录
async function updateOdds(pageId, odds) {
  const props = {};
  
  if (odds.jc) {
    props['竞彩欧赔胜'] = { number: odds.jc.win };
    props['竞彩欧赔平'] = { number: odds.jc.draw };
    props['竞彩欧赔负'] = { number: odds.jc.loss };
  }
  if (odds.bj) {
    props['百家欧赔胜'] = { number: odds.bj.win };
    props['百家欧赔平'] = { number: odds.bj.draw };
    props['百家欧赔负'] = { number: odds.bj.loss };
  }
  if (odds.iw) {
    props['Interwetten胜'] = { number: odds.iw.win };
    props['Interwetten平'] = { number: odds.iw.draw };
    props['Interwetten负'] = { number: odds.iw.loss };
  }
  
  if (Object.keys(props).length === 0) return false;
  
  const res = await notionRequest('PATCH', `/v1/pages/${pageId}`, { properties: props });
  return res.status === 200;
}

async function main() {
  const dates = ['2026-05-07', '2026-05-08', '2026-05-09', '2026-05-10', '2026-05-11'];
  let totalUpdated = 0;
  let totalFailed = 0;
  
  for (const dateStr of dates) {
    console.log(`\n=== ${dateStr} ===`);
    
    // 查询Notion记录
    const notionRecords = await queryByDate(dateStr);
    console.log(`Notion记录数: ${notionRecords.length}`);
    
    // 读取本地文件获取FID
    const taskDir = path.join(TASKS_DIR, dateStr);
    if (!fs.existsSync(taskDir)) {
      console.log(`  本地目录不存在，跳过`);
      continue;
    }
    
    const reportFiles = fs.readdirSync(taskDir).filter(f => f.endsWith('.md'));
    
    // 建立编号到FID的映射
    const fidMap = {};
    for (const rf of reportFiles) {
      const content = fs.readFileSync(path.join(taskDir, rf), 'utf8');
      const fidMatch = content.match(/FID[::]\s*(\d+)/);
      const numMatch = rf.match(/周[一二三四五六日](\d{3})/);
      if (fidMatch && numMatch) {
        fidMap[numMatch[1]] = fidMatch[1];
      }
    }
    
    // 处理每条记录
    for (const record of notionRecords) {
      const pageId = record.id;
      const notionName = record.properties['Name']?.title?.[0]?.plain_text || '';
      const numMatch = notionName.match(/(\d{3})/);
      const num = numMatch ? numMatch[1] : '';
      
      if (!num || !fidMap[num]) {
        console.log(`  ⏭️ 跳过 ${notionName} (无FID)`);
        continue;
      }
      
      const fid = fidMap[num];
      console.log(`  🔄 ${notionName} (FID:${fid})`);
      
      // 抓取赔率
      const odds = await fetchOddsFrom500(fid);
      
      if (odds && (odds.jc || odds.bj || odds.iw)) {
        const success = await updateOdds(pageId, odds);
        if (success) {
          console.log(`  ✅ 更新成功: 竞彩=${odds.jc?.win}/${odds.jc?.draw}/${odds.jc?.loss} 百家=${odds.bj?.win}/${odds.bj?.draw}/${odds.bj?.loss} IW=${odds.iw?.win}/${odds.iw?.draw}/${odds.iw?.loss}`);
          totalUpdated++;
        } else {
          console.log(`  ❌ 更新失败`);
          totalFailed++;
        }
      } else {
        console.log(`  ⚠️ 未获取到赔率数据`);
        totalFailed++;
      }
      
      // 限速: 每次请求间隔1秒
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  
  console.log(`\n=== 完成 ===`);
  console.log(`成功更新: ${totalUpdated} 条`);
  console.log(`失败: ${totalFailed} 条`);
}

main().catch(console.error);
