// Parse final report and sync to Notion database
// Usage: node parse_sync_notion.js test
// Target: 周三005_布雷斯特vs斯特拉斯.md

const https = require('https');
const fs = require('fs');
const path = require('path');

const NOTION_API_KEY = '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';
// Try both ID formats
const DB_ID_RAW = '35d91ad717ba80fba45ccb6471eaf4d9';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

const JINGCAI_DIR = path.join(__dirname);
const REPORT_FILE = path.join(JINGCAI_DIR, 'tasks', '2026-05-13', '周三005_布雷斯特vs斯特拉斯.md');

// 26 steps + final conclusion
const STEP_NAMES = [
  '第1步', '第2步', '第3步', '第4步', '第5步', '第6步',
  '第7步', '第8步', '第9步', '第10步', '第11步', '第12步',
  '第13步', '第14步', '第15步', '第16步', '第17步', '第18步',
  '第19步', '第20步', '第21步', '第22步', '第23步', '第24步',
  '第25步', '第26步', '最终结论'
];

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

// Parse report into 26 steps + conclusion
function parseReport(content) {
  const steps = {};
  
  // Extract each step by heading pattern
  // Step 1: ## 第1步: ...
  // Step 2: ## 第2步: ...
  // etc.
  
  // Define step boundaries based on report structure
  const stepPatterns = [
    { step: '第1步', pattern: /## 第1步[^\n]*?\n([\s\S]*?)(?=## 第2步)/ },
    { step: '第2步', pattern: /## 第2步[^\n]*?\n([\s\S]*?)(?=## 第3步)/ },
    { step: '第3步', pattern: /## 第3步[^\n]*?\n([\s\S]*?)(?=## 第4步)/ },
    { step: '第4步', pattern: /## 第4步[^\n]*?\n([\s\S]*?)(?=## 第5步)/ },
    { step: '第5步', pattern: /## 第5步[^\n]*?\n([\s\S]*?)(?=## 第6步)/ },
    { step: '第6步', pattern: /## 第6步[^\n]*?\n([\s\S]*?)(?=## 第7步)/ },
    { step: '第7步', pattern: /## 第7步[^\n]*?\n([\s\S]*?)(?=## 第8步)/ },
    { step: '第8步', pattern: /## 第8步[^\n]*?\n([\s\S]*?)(?=# 第四部分|# 第五部分|# 第六部分|# 第七部分|# 第八部分|# 第九部分)/ },
  ];
  
  // Alternative: use section-based parsing
  // Each "## 第X步" is a subheading under the main sections
  
  // Find all ## 第N步 headings and extract content between them
  const allStepRegex = /##\s+第(\d+)步[^\n]*?\n([\s\S]*?)(?=## 第\d+步|$)/g;
  let match;
  
  while ((match = allStepRegex.exec(content)) !== null) {
    const stepNum = parseInt(match[1]);
    const stepLabel = `第${stepNum}步`;
    let text = match[2].trim();
    
    // Truncate to max 2000 chars for Notion (rich_text limit per block)
    // We'll store the full text but limit for API
    if (text.length > 1800) {
      text = text.substring(0, 1800) + '\n...（已截断）';
    }
    
    steps[stepLabel] = text;
  }
  
  // Extract final conclusion (第九部分)
  const conclusionMatch = content.match(/# 第九部分[^\n]*?\n([\s\S]*?)$/);
  if (conclusionMatch) {
    let text = conclusionMatch[1].trim();
    // Remove trailing metadata lines
    text = text.replace(/\n---+[\s\S]*$/, '');
    if (text.length > 1800) {
      text = text.substring(0, 1800) + '\n...（已截断）';
    }
    steps['最终结论'] = text;
  }
  
  // Also extract metadata
  const meta = {};
  const dayMatch = content.match(/竞彩编号:\s*(.+)$/m);
  if (dayMatch) meta.竞彩编号 = dayMatch[1].trim();
  
  const leagueMatch = content.match(/比赛[::]\s*([^·\n]+)·/);
  if (leagueMatch) meta.联赛 = leagueMatch[1].trim();
  
  const teamsMatch = content.match(/#.*?vs(.+?)$/m);
  if (teamsMatch) {
    // Extract from title line
  }
  
  // Extract teams from filename pattern in content
  const titleMatch = content.match(/# 周[^\d]+(\d+)_([^v]+)vs(.+)/);
  if (titleMatch) {
    meta.竞彩编号 = meta.竞彩编号 || '周' + titleMatch[1];
    meta.主队 = titleMatch[2].trim();
    meta.客队 = titleMatch[3].replace(/\s*#.*/, '').trim();
  }
  
  const timeMatch = content.match(/比赛时间:\s*(.+)$/m);
  if (timeMatch) meta.比赛时间 = timeMatch[1].trim();
  
  const rqMatch = content.match(/让球:\s*(.+)$/m);
  if (rqMatch) meta.让球 = rqMatch[1].trim();
  
  const macauMatch = content.match(/澳门亚盘:\s*(.+)$/m);
  if (macauMatch) meta.澳门亚盘 = macauMatch[1].trim();
  
  // Extract prediction from conclusion
  const predMatch = content.match(/\*\*竞彩预测\*\*\s*\|\s*(.+?)(?=\n|$)/);
  if (predMatch) meta.竞彩预测 = predMatch[1].trim();
  
  const confMatch = content.match(/\*\*信心\*\*\s*\|\s*(.+?)(?=\n|$)/);
  if (confMatch) meta.竞彩信心 = confMatch[1].trim();
  
  return { steps, meta };
}

// Create Notion rich_text from markdown text
// Split into chunks of 2000 chars max each for Notion blocks
function richTextChunks(text) {
  if (!text) return [];
  const chunks = [];
  const maxLen = 1900;
  for (let i = 0; i < text.length; i += maxLen) {
    chunks.push({ text: { content: text.substring(i, i + maxLen) } });
  }
  return chunks;
}

// Check if database exists
async function checkDB() {
  console.log('Checking database...');
  const r = await notionRequest('GET', `/v1/databases/${DB_ID}`);
  console.log('Status:', r.status);
  if (r.status === 200) {
    console.log('DB Name:', r.data.title?.[0]?.plain_text || '?');
    const props = r.data.properties;
    console.log('Properties:', Object.keys(props).length);
    Object.keys(props).forEach(k => {
      console.log(`  ${k}: ${props[k].type}`);
    });
    return true;
  } else {
    console.log('Error:', JSON.stringify(r.data, null, 2).substring(0, 300));
    return false;
  }
}

// Create database with 26 step columns
async function createDBWithSteps() {
  // First create the database
  const parentPageId = '35d91ad7-17ba-80fba45ccb6471eaf4d9'; // This might be a parent page
  
  // Actually, let's check if it's a page first
  const r = await notionRequest('GET', `/v1/pages/${DB_ID}`);
  console.log('Page check status:', r.status);
  if (r.status === 200) {
    console.log('It is a page!');
    console.log(JSON.stringify(r.data.properties, null, 2).substring(0, 500));
    return r.data;
  }
  return null;
}

// Add a page to the database
async function addPage(databaseId, meta, steps) {
  // Build properties - 26 step columns + final conclusion
  const properties = {
    'Name': notionTitleProp(`${meta.竞彩编号 || ''} ${meta.主队 || ''}vs${meta.客队 || ''}`),
  };
  
  // Add meta fields
  if (meta.联赛) properties['联赛'] = notionSelectProp(meta.联赛);
  if (meta.主队) properties['主队'] = notionRichTextProp(meta.主队);
  if (meta.客队) properties['客队'] = notionRichTextProp(meta.客队);
  if (meta.竞彩预测) properties['竞彩预测'] = notionRichTextProp(meta.竞彩预测);
  if (meta.竞彩信心) properties['竞彩信心'] = notionRichTextProp(meta.竞彩信心);
  
  // Add 26 step columns
  for (let i = 1; i <= 26; i++) {
    const stepLabel = `第${i}步`;
    const propName = stepLabel;
    if (steps[stepLabel]) {
      properties[propName] = notionRichTextProp(steps[stepLabel]);
    } else {
      properties[propName] = { rich_text: [] };
    }
  }
  
  // Add final conclusion
  properties['最终结论'] = notionRichTextProp(steps['最终结论'] || '');
  
  const pageData = {
    parent: { database_id: databaseId },
    properties,
  };
  
  console.log('Creating page with properties:', Object.keys(properties).join(', '));
  
  const r = await notionRequest('POST', '/v1/pages', pageData);
  console.log('Status:', r.status);
  if (r.status === 200) {
    console.log('Page created:', r.data.id);
  } else {
    console.log('Error:', JSON.stringify(r.data, null, 2).substring(0, 500));
  }
  return r;
}

function notionTitleProp(text) {
  return { title: [{ text: { content: String(text) } }] };
}

function notionRichTextProp(text) {
  return text ? { rich_text: richTextChunks(text) } : { rich_text: [] };
}

function notionSelectProp(value) {
  return value ? { select: { name: String(value) } } : { select: null };
}

// Main
(async () => {
  console.log('Reading report:', REPORT_FILE);
  
  if (!fs.existsSync(REPORT_FILE)) {
    console.log('ERROR: Report file not found');
    return;
  }
  
  const content = fs.readFileSync(REPORT_FILE, 'utf8');
  console.log('Report length:', content.length, 'chars');
  
  const { steps, meta } = parseReport(content);
  console.log('Parsed steps:', Object.keys(steps).join(', '));
  console.log('Parsed meta:', JSON.stringify(meta));
  
  // Check step coverage
  for (let i = 1; i <= 26; i++) {
    const label = `第${i}步`;
    const has = steps[label] ? 'OK' : 'MISSING';
    console.log(`  ${label}: ${has} (${steps[label]?.length || 0} chars)`);
  }
  console.log(`  最终结论: ${steps['最终结论'] ? 'OK' : 'MISSING'} (${steps['最终结论']?.length || 0} chars)`);
  
  console.log('\n--- Notion DB Check ---');
  const dbOk = await checkDB();
  
  if (!dbOk) {
    console.log('\nDatabase not found. Checking if it is a page...');
    const page = await createDBWithSteps();
  }
  
  console.log('\n--- Adding page ---');
  const result = await addPage(DB_ID, meta, steps);
})();
