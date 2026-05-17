const fs = require('fs');
const path = require('path');

const baseDir = 'C:\\Users\\lianjie\\.openclaw\\workspace\\jingcai\\tasks';

// 04-29 scores from screenshot
const scores = {
  '周三002': '1:0',
  '周三003': '1:2',
  '周三004': '1:2',
  '周三005': '1:0',
  '周三006': '2:0',
  '周三007': '2:1',
  '周三008': '2:0',
  '周三009': '0:1',
  '周三010': '1:1',
  '周三011': '1:1',
  '周三012': '1:0',
};

const date = '2026-04-29';
const dataDir = path.join(baseDir, date, 'data');

let updated = 0, modified = 0;

for (const [matchNum, score] of Object.entries(scores)) {
  const allDirs = fs.readdirSync(dataDir).filter(d => {
    const fullPath = path.join(dataDir, d);
    return fs.statSync(fullPath).isDirectory() && d.startsWith('match');
  });
  
  for (const d of allDirs) {
    const metaPath = path.join(dataDir, d, 'meta.json');
    if (!fs.existsSync(metaPath)) continue;
    try {
      const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
      if (meta.matchnum === matchNum) {
        const oldScore = meta.score || '';
        if (oldScore !== score) {
          meta.score = score;
          fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2));
          modified++;
          console.log(`${matchNum}: ${oldScore || '(无)'} → ${score}`);
        } else {
          console.log(`${matchNum}: ${score} (已存在)`);
        }
        updated++;
        break;
      }
    } catch (e) {}
  }
}

console.log(`\n${date}: 匹配${updated}场, 修改${modified}场`);

// Count total
let totalMatches = 0, totalWithScores = 0;
const allDates = fs.readdirSync(baseDir).filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort();
const byDate = {};
for (const dt of allDates) {
  const dd = path.join(baseDir, dt, 'data');
  if (!fs.existsSync(dd)) continue;
  const dirs = fs.readdirSync(dd).filter(d => {
    const fullPath = path.join(dd, d);
    return fs.statSync(fullPath).isDirectory() && d.startsWith('match');
  });
  let dtTotal = 0, dtScored = 0;
  for (const d of dirs) {
    const mp = path.join(dd, d, 'meta.json');
    if (!fs.existsSync(mp)) continue;
    try {
      const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
      if (m.matchnum) {
        dtTotal++;
        if (m.score) dtScored++;
      }
    } catch (e) {}
  }
  totalMatches += dtTotal;
  totalWithScores += dtScored;
  byDate[dt] = `${dtScored}/${dtTotal}`;
}

console.log(`\n总场次: ${totalMatches}, 有比分: ${totalWithScores}, 无比分: ${totalMatches - totalWithScores}`);
console.log(`\n按日期:`);
for (const [d, c] of Object.entries(byDate)) {
  console.log(`  ${d}: ${c}`);
}
