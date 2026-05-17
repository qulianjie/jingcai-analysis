const fs = require('fs');
const path = require('path');

// 从截图识别的比分数据
const scoresFromImage = {
    '05-01': {
        '周五001': '1:0',
        '周五002': '1:0',
        '周五003': '2:0',
        '周五004': '2:2',
        '周五005': '2:0',
        '周五006': '1:0',
        '周五007': '0:0',
        '周五008': '3:2',
        '周五009': '2:1',
        '周五010': '1:0',
        '周五011': '0:0',
        '周五012': '3:2',
    },
    '05-02': {
        '周六001': '1:1',
    },
};

// 更新meta.json
const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
let updated = 0;

// 日期映射: 2026-05-01 -> 05-01, 2026-05-02 -> 05-02
const dateMap = {
    '2026-05-01': '05-01',
    '2026-05-02': '05-02',
};

for (const [dateDir, shortDate] of Object.entries(dateMap)) {
    const scores = scoresFromImage[shortDate];
    if (!scores) continue;
    
    const dp = path.join(BASE, dateDir);
    if (!fs.existsSync(dp)) continue;
    
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) continue;
    
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        if (!fs.existsSync(metaPath)) continue;
        
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        const matchnum = meta.matchnum || '';
        
        if (scores[matchnum]) {
            const newScore = scores[matchnum];
            const oldScore = meta.score || '(无)';
            meta.score = newScore;
            fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
            updated++;
            console.log(`${dateDir} ${matchnum}: ${oldScore} → ${newScore}`);
        }
    }
}

console.log(`\n总更新: ${updated}场`);

// 统计当前比分情况
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
console.log(`\n总场次: ${total}, 有比分: ${withScore}, 无比分: ${total - withScore}`);
