const fs = require('fs');
const path = require('path');

// 从截图识别的所有比分数据
const allScores = {
    '2026-04-01': {
        '周四001': '2:1', '周四002': '1:0', '周四003': '3:0',
        '周四004': '1:0', '周四005': '2:1', '周四006': '1:0',
        '周四007': '2:1', '周四008': '1:1', '周四009': '3:2',
        '周四010': '2:2',
    },
    '2026-04-02': {
        '周五001': '2:1', '周五002': '1:0', '周五003': '1:1',
        '周五004': '1:2', '周五005': '1:1', '周五006': '0:1',
        '周五007': '1:2', '周五008': '1:1', '周五009': '3:1',
        '周五010': '2:2', '周五011': '2:0', '周五012': '1:1',
    },
    '2026-04-03': {
        '周六001': '3:0', '周六002': '2:2', '周六003': '1:1',
        '周六004': '1:1', '周六005': '2:1', '周六006': '0:1',
        '周六007': '1:2', '周六008': '1:1', '周六009': '0:0',
        '周六010': '1:1', '周六011': '3:1', '周六012': '1:1',
    },
    '2026-04-04': {
        '周日001': '2:1', '周日002': '2:1', '周日003': '1:1',
        '周日004': '2:2', '周日005': '2:1', '周日006': '1:0',
        '周日007': '2:2', '周日008': '1:1', '周日009': '1:1',
    },
    '2026-04-05': {
        '周一001': '2:1', '周一002': '1:0', '周一003': '2:2',
        '周一004': '2:0', '周一005': '1:1', '周一006': '2:2',
        '周一007': '1:2', '周一008': '3:1',
    },
    '2026-04-06': {
        '周二001': '1:1', '周二002': '2:1', '周二003': '2:0',
        '周二004': '3:2', '周二005': '1:1', '周二006': '2:2',
        '周二007': '2:1', '周二008': '1:1', '周二009': '3:2',
        '周二010': '1:2', '周二011': '3:2', '周二012': '1:0',
    },
    '2026-04-07': {
        '周三001': '1:1', '周三002': '1:1', '周三003': '2:0',
        '周三004': '1:1', '周三005': '2:0', '周三006': '1:0',
        '周三007': '2:0', '周三008': '1:1', '周三009': '3:1',
        '周三010': '1:0', '周三011': '3:0',
    },
    '2026-04-08': {
        '周四001': '2:0', '周四002': '1:0', '周四003': '2:1',
        '周四004': '0:0', '周四005': '2:2', '周四006': '1:0',
        '周四007': '1:0',
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

const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';

// 检查每个日期是否有data目录和match目录
const hasData = {};
for (const d of fs.readdirSync(BASE).sort()) {
    const dp = path.join(BASE, d);
    if (!fs.statSync(dp).isDirectory()) continue;
    const dataDir = path.join(dp, 'data');
    if (fs.existsSync(dataDir)) {
        const matches = fs.readdirSync(dataDir).filter(m => m.startsWith('match'));
        if (matches.length > 0) {
            // 检查第一个match是否有meta.json
            const firstMatch = path.join(dataDir, matches[0]);
            const hasMeta = fs.existsSync(path.join(firstMatch, 'meta.json'));
            hasData[d] = { count: matches.length, hasMeta };
        }
    }
}

console.log('=== 各日期数据状态 ===');
for (const [d, info] of Object.entries(hasData)) {
    console.log(`  ${d}: ${info.count}场 (meta.json: ${info.hasMeta ? '✅' : '❌'})`);
}

// 更新比分
let updated = 0, changed = 0, skipped = 0;

for (const [dateDir, scores] of Object.entries(allScores)) {
    const dp = path.join(BASE, dateDir);
    if (!fs.existsSync(dp)) {
        console.log(`\n${dateDir}: ❌ 目录不存在`);
        continue;
    }
    
    const dataDir = path.join(dp, 'data');
    if (!fs.existsSync(dataDir)) {
        console.log(`\n${dateDir}: ❌ 没有data目录`);
        continue;
    }
    
    console.log(`\n${dateDir}:`);
    let matched = 0, dateChanged = 0;
    
    for (const m of fs.readdirSync(dataDir).sort()) {
        if (!m.startsWith('match')) continue;
        const metaPath = path.join(dataDir, m, 'meta.json');
        
        if (!fs.existsSync(metaPath)) {
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
                dateChanged++;
            }
            matched++;
            updated++;
        }
    }
    
    console.log(`  匹配${matched}场 (修改${dateChanged})`);
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

console.log(`\n========================`);
console.log(`总更新: ${updated}场 (实际修改: ${changed})`);
console.log(`总场次: ${total}, 有比分: ${withScore}, 无比分: ${total - withScore}`);

console.log(`\n各日期比分进度:`);
for (const [d, s] of Object.entries(dateStats).sort()) {
    const bar = '█'.repeat(Math.floor(parseInt(s) / total * 50)) || '';
    console.log(`  ${d}: ${s.padStart(6)} ${bar}`);
}
