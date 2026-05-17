const fs = require('fs');
const path = require('path');
const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
let total = 0, withScore = 0;
for (const d of fs.readdirSync(BASE).sort()) {
    const dp = path.join(BASE, d);
    if (!fs.statSync(dp).isDirectory()) continue;
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) continue;
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        if (!fs.existsSync(metaPath)) continue;
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        total++;
        if (meta.score && meta.score.includes(':')) withScore++;
    }
}
console.log(`总场次: ${total}, 有比分: ${withScore}, 无比分: ${total - withScore}`);
