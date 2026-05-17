// Parse final report into 26 steps + final conclusion
// Usage: node parse_steps.js

const fs = require('fs');
const path = require('path');

const REPORT_FILE = path.join(__dirname, 'tasks', '2026-05-13', '周三005_布雷斯特vs斯特拉斯.md');

const content = fs.readFileSync(REPORT_FILE, 'utf8');

// Step 1-8: use ## 第N步 pattern
// Step 9-13: 第四部分 - 主队主场分析
//   第9步: "主队主场・相同联赛・澳门亚盘同赔" section
//   第10步: "## 第十步"
//   第11步: "## 第十一步"
//   第12步: "## 第十二步"
//   第13步: "## 第十三步"
// Step 14-18: 第五部分 - 客队客场分析
//   第14步: "客队客场・相同联赛・澳门亚盘同赔" section
//   第15步: "## 第十五步"
//   第16步: "## 第十六步"
//   第17步: "## 第十七步"
//   第18步: "## 第十八步"
// Step 19-23: 第六部分 - 百家对比分析
//   第19步: 百家对比 section (no heading)
//   第20步: "## 第二十步"
//   第21步: "## 第二十一步"
//   第22步: (implicit in 百家对比)
//   第23步: "## 第二十三步"
// Step 24: 第七部分 - 盘路完全匹配汇总
// Step 25: 第八部分 - 庄家盈亏分析
// Step 26: 第八部分续 - 庄家盈亏占比分析
// Final: 第九部分 - 最终结论

// Strategy: use section-based parsing with Chinese numerals
const steps = {};

// Helper: extract text between two markers
function extractBetween(startMarker, endMarker) {
  const startIdx = content.indexOf(startMarker);
  if (startIdx < 0) return '';
  let endIdx;
  if (endMarker) {
    endIdx = content.indexOf(endMarker, startIdx + startMarker.length);
  } else {
    endIdx = content.length;
  }
  if (endIdx < 0) endIdx = content.length;
  return content.substring(startIdx, endIdx).trim();
}

// Step 1-8: ## 第N步
for (let i = 1; i <= 8; i++) {
  const heading = `## 第${i}步`;
  const nextHeading = i < 8 ? `## 第${i+1}步` : '# 第四部分';
  const startIdx = content.indexOf(heading);
  if (startIdx >= 0) {
    const nextIdx = content.indexOf(nextHeading, startIdx + heading.length);
    const endIdx = nextIdx >= 0 ? nextIdx : content.length;
    steps[`第${i}步`] = content.substring(startIdx, endIdx).trim();
  }
}

// Step 9: 第四部分 - 主队主场 (first section before 第十步)
const s9Start = content.indexOf('# 第四部分');
const s10Start = content.indexOf('## 第十步');
if (s9Start >= 0 && s10Start >= 0) {
  steps['第9步'] = content.substring(s9Start, s10Start).trim();
}

// Step 10-13: 第十步 to 第十三步
for (let i = 10; i <= 13; i++) {
  const chineseNums = ['十','十一','十二','十三','十四','十五','十六','十七','十八','十九','二十','二十一','二十二','二十三','二十四','二十五','二十六'];
  const idx = i - 10;
  const heading = `## 第${chineseNums[idx]}步`;
  const nextHeading = i < 13 ? `## 第${chineseNums[idx+1]}步` : '# 第五部分';
  const startIdx = content.indexOf(heading);
  if (startIdx >= 0) {
    const nextIdx = content.indexOf(nextHeading, startIdx + heading.length);
    const endIdx = nextIdx >= 0 ? nextIdx : content.length;
    steps[`第${i}步`] = content.substring(startIdx, endIdx).trim();
  }
}

// Step 14: 第五部分 - 客队客场 (first section before 第十五步)
const s14Start = content.indexOf('# 第五部分');
const s15Start = content.indexOf('## 第十五步');
if (s14Start >= 0 && s15Start >= 0) {
  steps['第14步'] = content.substring(s14Start, s15Start).trim();
}

// Step 15-18: 第十五步 to 第十八步
for (let i = 15; i <= 18; i++) {
  const chineseNums = ['十五','十六','十七','十八','十九','二十','二十一','二十二','二十三','二十四','二十五','二十六'];
  const idx = i - 15;
  const heading = `## 第${chineseNums[idx]}步`;
  const nextHeading = i < 18 ? `## 第${chineseNums[idx+1]}步` : '# 第六部分';
  const startIdx = content.indexOf(heading);
  if (startIdx >= 0) {
    const nextIdx = content.indexOf(nextHeading, startIdx + heading.length);
    const endIdx = nextIdx >= 0 ? nextIdx : content.length;
    steps[`第${i}步`] = content.substring(startIdx, endIdx).trim();
  }
}

// Step 19: 第六部分 - 百家对比分析 (before 第二十步)
const s19Start = content.indexOf('# 第六部分');
const s20Start = content.indexOf('## 第二十步');
if (s19Start >= 0 && s20Start >= 0) {
  steps['第19步'] = content.substring(s19Start, s20Start).trim();
}

// Step 20-21: 第二十步, 第二十一步
for (let i = 20; i <= 21; i++) {
  const chineseNums = ['二十','二十一','二十二','二十三','二十四','二十五','二十六'];
  const idx = i - 20;
  const heading = `## 第${chineseNums[idx]}步`;
  const nextHeading = i < 21 ? `## 第${chineseNums[idx+1]}步` : '# 第七部分';
  const startIdx = content.indexOf(heading);
  if (startIdx >= 0) {
    const nextIdx = content.indexOf(nextHeading, startIdx + heading.length);
    const endIdx = nextIdx >= 0 ? nextIdx : content.length;
    steps[`第${i}步`] = content.substring(startIdx, endIdx).trim();
  }
}

// Step 22: between 第二十一步 end and 第二十三步 start
const s21EndIdx = content.indexOf('## 第二十三步');
const s22StartIdx = content.indexOf('## 第二十一步');
if (s22StartIdx >= 0 && s21EndIdx >= 0) {
  steps['第22步'] = content.substring(s22StartIdx, s21EndIdx).trim();
}

// Step 23: 第二十三步
const s23Heading = '## 第二十三步';
const s23StartIdx = content.indexOf(s23Heading);
if (s23StartIdx >= 0) {
  const nextIdx = content.indexOf('# 第七部分', s23StartIdx + s23Heading.length);
  const endIdx = nextIdx >= 0 ? nextIdx : content.length;
  steps['第23步'] = content.substring(s23StartIdx, endIdx).trim();
}

// Step 24: 第七部分 - 盘路完全匹配汇总
const s24Start = content.indexOf('# 第七部分');
const s25Start = content.indexOf('# 第八部分:');
if (s24Start >= 0 && s25Start >= 0) {
  steps['第24步'] = content.substring(s24Start, s25Start).trim();
}

// Step 25: 第八部分 - 庄家盈亏分析
const s25Heading = '# 第八部分: 庄家盈亏分析';
const s26Heading = '# 第八部分续: 庄家盈亏占比分析';
const s25Idx = content.indexOf(s25Heading);
const s26Idx = content.indexOf(s26Heading);
if (s25Idx >= 0 && s26Idx >= 0) {
  steps['第25步'] = content.substring(s25Idx, s26Idx).trim();
}

// Step 26: 第八部分续 - 庄家盈亏占比分析
const s27Start = content.indexOf('# 第九部分');
if (s26Idx >= 0 && s27Start >= 0) {
  steps['第26步'] = content.substring(s26Idx, s27Start).trim();
}

// Final conclusion: 第九部分
if (s27Start >= 0) {
  let conclusion = content.substring(s27Start).trim();
  // Remove trailing metadata
  conclusion = conclusion.replace(/\n---+[\s\S]*$/, '');
  steps['最终结论'] = conclusion;
}

// Output results
console.log('Parsed steps:');
for (let i = 1; i <= 26; i++) {
  const label = `第${i}步`;
  const has = steps[label] ? 'OK' : 'MISSING';
  const len = steps[label]?.length || 0;
  console.log(`  ${label}: ${has} (${len} chars)`);
}
console.log(`  最终结论: ${steps['最终结论'] ? 'OK' : 'MISSING'} (${steps['最终结论']?.length || 0} chars)`);

// Save to JSON for use by sync script
const output = JSON.stringify(steps, null, 2);
fs.writeFileSync(path.join(__dirname, 'parsed_steps.json'), output, 'utf8');
console.log('\nSaved to parsed_steps.json');
