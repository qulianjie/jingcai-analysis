const fs = require('fs');
const path = require('path');

const baseDir = 'C:\\Users\\lianjie\\.openclaw\\workspace\\jingcai\\tasks';

// Batch 2 scores from 8 screenshots
const scores = {
  '2026-05-03': {
    '周日001': '1:1',
    '周日002': '2:1',
    '周日003': '0:2',
    '周日004': '2:0',
    '周日005': '0:0',
    '周日006': '1:0',
    '周日007': '3:3',
    '周日008': '4:1',
    '周日009': '2:1',
    '周日010': '3:0',
    '周日011': '1:1',
    '周日012': '4:1',
    '周日013': '1:0',
    '周日014': '0:1',
    '周日015': '1:2',
    '周日016': '1:1',
    '周日017': '1:1',
    '周日018': '0:1',
    '周日019': '0:3',
  },
  '2026-05-04': {
    '周一001': '1:1',
    '周一002': '2:1',
    '周一003': '1:1',
    '周一004': '0:1',
    '周一005': '1:2',
    '周一006': '1:0',
    '周一007': '2:0',
    '周一008': '2:2',
    '周一009': '2:3',
    '周一010': '3:1',
    '周一011': '0:0',
    '周一012': '2:3',
  },
  '2026-05-05': {
    '周二001': '2:0',
    '周二002': '0:0',
    '周二003': '0:1',
    '周二004': '3:0',
    '周二005': '2:2',
    '周二006': '0:3',
    '周二007': '2:3',
    '周二008': '1:4',
    '周二009': '0:1',
    '周二010': '1:1',
    '周二011': '2:0',
  },
};

let totalUpdated = 0, totalModified = 0, totalMatched = 0;

for (const [date, matchScores] of Object.entries(scores)) {
  const dataDir = path.join(baseDir, date, 'data');
  if (!fs.existsSync(dataDir)) continue;

  let dateMatched = 0;
  
  // Find match directories
  const dirs = fs.readdirSync(dataDir).filter(d => d.startsWith('match') || d.startsWith('group') || d.startsWith('step'));
  
  for (const [matchNum, score] of Object.entries(matchScores)) {
    // Find matching directory by scanning meta.json
    const allDirs = fs.readdirSync(dataDir);
    for (const d of allDirs) {
      const metaPath = path.join(dataDir, d, 'meta.json');
      if (!fs.existsSync(metaPath)) continue;
      try {
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        if (meta.matchnum === matchNum) {
          const oldScore = meta.score || '';
          meta.score = score;
          if (oldScore !== score) {
            fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2));
            totalModified++;
            console.log(`${date} ${matchNum}: ${oldScore || '(无)'} → ${score}`);
          } else {
            console.log(`${date} ${matchNum}: ${score} (已存在)`);
          }
          totalUpdated++;
          dateMatched++;
          totalMatched++;
          break;
        }
      } catch (e) {}
    }
  }
  
  console.log(`${date}: 匹配${dateMatched}场`);
}

// Count total scores
let totalMatches = 0, totalWithScores = 0;
const byDate = {};
const allDates = fs.readdirSync(baseDir).filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort();
for (const date of allDates) {
  const dataDir = path.join(baseDir, date, 'data');
  if (!fs.existsSync(dataDir)) continue;
  const dirs = fs.readdirSync(dataDir);
  let dateTotal = 0, dateScored = 0;
  for (const d of dirs) {
    const metaPath = path.join(dataDir, d, 'meta.json');
    if (!fs.existsSync(metaPath)) continue;
    try {
      const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
      if (meta.matchnum) {
        dateTotal++;
        if (meta.score) dateScored++;
      }
    } catch (e) {}
  }
  totalMatches += dateTotal;
  totalWithScores += dateScored;
  byDate[date] = `${dateScored}/${dateTotal}`;
}

console.log(`\n总更新: ${totalUpdated}场 (实际修改: ${totalModified}场)`);
console.log(`\n总场次: ${totalMatches}, 有比分: ${totalWithScores}, 无比分: ${totalMatches - totalWithScores}`);
console.log(`\n按日期统计:`);
for (const [d, c] of Object.entries(byDate)) {
  console.log(`  ${d}: ${c}`);
}
