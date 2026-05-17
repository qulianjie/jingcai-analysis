const fs = require('fs');
const path = require('path');

// 从截图识别的比分数据（04-24到04-30）
const scoresFromImage = {
    '2026-04-24': {
        '周四001': '0:2', '周四002': '1:1', '周四003': '1:1',
        '周四004': '0:0', '周四005': '2:2', '周四006': '0:0',
        '周四007': '2:2', '周四008': '1:1', '周四009': '1:0',
        '周四010': '1:0',
    },
    '2026-04-25': {
        '周五001': '2:1', '周五002': '2:1', '周五003': '2:2',
        '周五004': '1:1', '周五005': '1:0', '周五006': '1:1',
        '周五007': '2:2', '周五008': '1:0', '周五009': '3:0',
        '周五010': '2:0', '周五011': '2:2', '周五012': '1:1',
    },
    '2026-04-26': {
        '周六001': '3:2', '周六002': '1:2', '周六003': '1:1',
        '周六004': '2:0', '周六005': '1:0', '周六006': '1:2',
        '周六007': '1:1', '周六008': '1:2', '周六009': '2:0',
        '周六010': '1:0', '周六011': '3:0', '周六012': '1:0',
    },
    '2026-04-27': {
        '周日001': '2:2', '周日002': '0:0', '周日003': '2:0',
        '周日004': '2:1', '周日005': '0:0', '周日006': '2:1',
        '周日007': '3:2', '周日008': '3:2', '周日009': '2:2',
        '周日010': '1:1', '周日011': '1:0', '周日012': '1:0',
    },
    '2026-04-28': {
        '周一001': '0:1', '周一002': '2:0', '周一003': '1:1',
        '周一004': '1:1', '周一005': '2:0', '周一006': '0:0',
        '周一007': '1:0', '周一008': '3:1', '周一009': '2:0',
    },
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
};

// 更新meta.json
const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
let updated = 0;
let changed = 0;

for (const [dateDir, scores] of Object.entries(scoresFromImage)) {
    const dp = path.join(BASE, dateDir);
    if (!fs.existsSync(dp)) {
        console.log(`${dateDir}: 目录不存在，跳过`);
        continue;
    }
    
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) continue;
    
    let dateUpdated = 0;
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        if (!fs.existsSync(metaPath)) continue;
        
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        const matchnum = meta.matchnum || '';
        
        if (scores[matchnum]) {
            const newScore = scores[matchnum];
            const oldScore = meta.score || '(无)';
            if (oldScore !== newScore) {
                if (oldScore !== '(无)') changed++;
                meta.score = newScore;
                fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
            }
            updated++;
            dateUpdated++;
        }
    }
    if (dateUpdated > 0) console.log(`${dateDir}: 更新${dateUpdated}场`);
}

console.log(`\n总更新: ${updated}场 (修改: ${changed}场)`);

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
