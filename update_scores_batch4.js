const fs = require('fs');
const path = require('path');

// 从截图识别的比分数据
const scoresFromImage = {
    '2026-04-29': {
        '周二001': '1:1', '周二002': '0:2', '周二003': '3:1',
        '周二004': '1:2', '周二005': '2:2', '周二006': '1:0',
        '周二007': '2:1', '周二008': '1:2', '周二009': '2:2',
        '周二010': '2:1', '周二011': '3:1',
    },
    '2026-04-30': {
        '周三001': '0:2', '周三002': '1:2', '周三003': '0:0',
        '周三004': '1:1', '周三005': '1:0', '周三006': '0:2',
        '周三007': '1:0', '周三008': '3:1', '周三009': '1:1',
        '周三010': '2:2', '周三011': '2:1', '周三012': '1:1',
    },
    '2026-05-01': {
        '周五001': '1:0', '周五002': '1:0', '周五003': '2:0',
        '周五004': '2:2', '周五005': '2:0', '周五006': '1:0',
        '周五007': '0:0', '周五008': '3:2', '周五009': '2:1',
        '周五010': '1:0', '周五011': '0:0', '周五012': '3:2',
    },
    '2026-05-02': {
        '周六001': '1:1',
    },
};

// 更新meta.json（只对有meta.json的日期）
const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
let updated = 0;
let changed = 0;
const noMetaDates = [];

for (const [dateDir, scores] of Object.entries(scoresFromImage)) {
    const dp = path.join(BASE, dateDir);
    if (!fs.existsSync(dp)) continue;
    
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) continue;
    
    let dateMatched = 0;
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        
        // 检查meta.json是否存在
        if (!fs.existsSync(metaPath)) {
            if (dateMatched === 0) noMetaDates.push(dateDir);
            continue;
        }
        
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        const matchnum = meta.matchnum || '';
        
        if (scores[matchnum]) {
            const newScore = scores[matchnum];
            const oldScore = meta.score || '(无)';
            if (oldScore !== newScore) {
                meta.score = newScore;
                fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
                changed++;
            }
            updated++;
            dateMatched++;
        }
    }
    console.log(`${dateDir}: 匹配${dateMatched}场`);
}

console.log(`\n总更新: ${updated}场 (实际修改: ${changed}场)`);
if (noMetaDates.length > 0) {
    console.log(`无meta.json的日期: ${noMetaDates.join(', ')}`);
}

// 统计比分情况
let total = 0, withScore = 0;
const dateStats = {};
for (const d of fs.readdirSync(BASE).sort()) {
    const dp = path.join(BASE, d);
    if (!fs.statSync(dp).isDirectory()) continue;
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) continue;
    let t = 0, w = 0;
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        if (!fs.existsSync(metaPath)) continue;
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        t++;
        if (meta.score && meta.score.includes(':')) w++;
    }
    if (t > 0) {
        dateStats[d] = `${w}/${t}`;
        total += t;
        withScore += w;
    }
}

console.log(`\n总场次: ${total}, 有比分: ${withScore}, 无比分: ${total - withScore}`);
console.log(`\n按日期: ${Object.entries(dateStats).map(([k,v])=>`${k}(${v})`).join(', ')}`);
