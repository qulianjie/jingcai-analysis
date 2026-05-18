// 检查让球预测提取
const fs = require('fs');
const path = require('path');

const f = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-02/周六001_奥克兰FCvs墨尔本城.md';
const content = fs.readFileSync(f, 'utf-8');

// Find 让球预测
const rq_match = content.match(/\*\*让球预测\*\*\s*\|\s*([^\|]+)/);
console.log('Match found:', !!rq_match);
if (rq_match) {
    console.log('Full match:', JSON.stringify(rq_match[0]));
    console.log('Group 1:', JSON.stringify(rq_match[1]));
}

// Show context around 让球预测
const idx = content.indexOf('让球预测');
if (idx >= 0) {
    console.log('\nContext:');
    console.log(content.substring(idx, idx + 100));
}
