const fs = require('fs');
const path = require('path');
const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';

for (const d of fs.readdirSync(BASE).sort()) {
    const dp = path.join(BASE, d);
    if (!fs.statSync(dp).isDirectory()) continue;
    const dataDir = path.join(dp, 'data');
    if (fs.existsSync(dataDir)) {
        const matches = fs.readdirSync(dataDir).filter(m => m.startsWith('match'));
        if (matches.length > 0) {
            console.log(`${d}: ${matches.length}场 (有data目录)`);
        }
    }
}
