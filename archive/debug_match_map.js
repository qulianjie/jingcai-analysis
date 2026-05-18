// 修复: sync_notion.js 的 match目录匹配逻辑
// 从meta.json读取matchnum，匹配对应的竞彩编号（如周六022→022）

const fs = require('fs');
const path = require('path');
const dataDir = path.join(__dirname, 'tasks', '2026-05-09', 'data');
const dirs = fs.readdirSync(dataDir).filter(d => d.startsWith('match') && fs.statSync(path.join(dataDir, d)).isDirectory());

// Build mapping: matchnum → matchDir
const map = {};
for (const d of dirs) {
  const metaPath = path.join(dataDir, d, 'meta.json');
  if (!fs.existsSync(metaPath)) continue;
  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  const mn = meta.matchnum || '';
  // 提取编号数字: 周六022 → 022
  const m = mn.match(/(\d{3})/);
  if (m) {
    const num = m[1]; // "022"
    if (!map[num]) map[num] = [];
    map[num].push({ dir: d, meta });
  }
}

// Show all mappings
for (const [num, entries] of Object.entries(map).sort()) {
  for (const e of entries) {
    console.log(`${num} → ${e.dir} (${e.meta.matchnum || '?'})`);
  }
}
