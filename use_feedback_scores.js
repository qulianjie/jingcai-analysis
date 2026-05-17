const fs = require('fs');
const path = require('path');

// 读取本地feedback缓存
const feedbackDir = 'C:/Users/lianjie/.openclaw/workspace/data/jingcai';
const files = fs.readdirSync(feedbackDir).filter(f => f.startsWith('feedback_') && f.endsWith('.json'));

console.log(`反馈缓存文件: ${files.length}个`);

const allScores = {};

for (const f of files) {
    try {
        const data = JSON.parse(fs.readFileSync(path.join(feedbackDir, f), 'utf8'));
        if (data.matches) {
            for (const m of data.matches) {
                if (m.matchnum && m.score) {
                    allScores[m.matchnum] = m.score;
                }
            }
            console.log(`${f}: ${data.matches.length}场, 有比分: ${data.matches.filter(m=>m.score).length}场`);
        }
    } catch (e) {
        console.log(`${f}: parse error`);
    }
}

console.log(`\n总唯一比分: ${Object.keys(allScores).length}场`);
for (const [k, v] of Object.entries(allScores).sort()) {
    console.log(`  ${k}: ${v}`);
}

// 写入meta.json
const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
let updated = 0;

for (const d of fs.readdirSync(BASE).sort()) {
    const dp = path.join(BASE, d);
    if (!fs.statSync(dp).isDirectory()) continue;
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) continue;
    
    let dateUpdated = 0;
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        if (!fs.existsSync(metaPath)) continue;
        
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        const matchnum = meta.matchnum || '';
        
        if (allScores[matchnum]) {
            meta.score = allScores[matchnum];
            fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
            updated++;
            dateUpdated++;
        }
    }
    if (dateUpdated > 0) console.log(`  ${d}: 更新${dateUpdated}场`);
}

console.log(`\n总更新: ${updated}场`);

// 现在跑分析
console.log('\n重新跑组合分析...\n');
