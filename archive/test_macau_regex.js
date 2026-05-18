// Test the updated regex
const fs = require('fs');

const reportPath = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15/周五002_达马克vs迈季迈阿宽广.md';
const content = fs.readFileSync(reportPath, 'utf8');

// Find all lines with 澳门亚盘
const lines = content.split('\n').filter(l => l.includes('澳门亚盘') && l.includes('|'));
console.log('Lines with 澳门亚盘:');
lines.forEach((l, i) => console.log(`  ${i}: ${l.trim()}`));

// Test the updated regex
const trendM = content.match(/\|\s*澳门亚盘\s*\|\s*([+-][\d.]+\s+[^|]+)\s*\|\s*([\d.]+%)\s*\|/);
console.log('\nUpdated regex match:', trendM ? trendM[1].trim() + ' | ' + trendM[2].trim() : '(empty)');

// Test the old regex (利好[主客])
const oldM = content.match(/\|\s*澳门亚盘\s*\|\s*([+-][\d.]+\s+利好[主客])\s*\|\s*([\d.]+%)\s*\|/);
console.log('Old regex match:', oldM ? oldM[1].trim() + ' | ' + oldM[2].trim() : '(empty)');
