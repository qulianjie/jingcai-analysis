// Check 周五002 conclusion section
const fs = require('fs');
const path = require('path');

const reportPath = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15/周五002_达马克vs迈季迈阿宽广.md';
const content = fs.readFileSync(reportPath, 'utf8');

// Find all lines with 澳门亚盘
const lines = content.split('\n').filter(l => l.includes('澳门亚盘'));
console.log('All lines with 澳门亚盘:');
lines.forEach((l, i) => console.log(`  ${i}: ${l.trim()}`));

// Check conclusion section regex
const conclusionSection = content.match(/# [\u4e5d9][\u90e8\u9879\u5206\u7ae0][\s\S]*?(?=# [^\u4e5d9]|$)/);
console.log('\nConclusion section found:', !!conclusionSection);
if (conclusionSection) {
    const cs = conclusionSection[0];
    console.log('Length:', cs.length);
    console.log('First 200 chars:', cs.substring(0, 200));
    
    // Check for 澳门亚盘 in conclusion
    const macauInConclusion = cs.match(/\|\s*澳门亚盘\s*\|/);
    console.log('澳门亚盘 in conclusion:', !!macauInConclusion);
    
    // Find all table rows in conclusion
    console.log('\nTable rows in conclusion:');
    cs.split('\n').filter(l => l.includes('|') && l.trim().startsWith('|')).forEach(l => {
        console.log('  ' + l.trim().substring(0, 100));
    });
}
