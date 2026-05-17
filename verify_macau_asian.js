// Verify: test extractScoreFromTable with updated regex on all 05-16 reports
const fs = require('fs');
const path = require('path');

const tasksDir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16';
const reports = fs.readdirSync(tasksDir).filter(f => f.endsWith('.md') && f !== 'sunday_matches.md');

let okCount = 0;
let emptyCount = 0;

for (const report of reports.sort()) {
    const reportPath = path.join(tasksDir, report);
    const content = fs.readFileSync(reportPath, 'utf8');
    
    // The updated extractScoreFromTable regex (same as in sync_notion.js now)
    const trendM = content.match(/\|\s*澳门亚盘\s*\|\s*([+-][\d.]+\s+[^|]+)\s*\|\s*([\d.]+%)\s*\|/);
    const macau_asian = trendM ? trendM[1].trim() + ' | ' + trendM[2].trim() : '';
    
    if (macau_asian) {
        okCount++;
        console.log(`${report}: ✅ ${macau_asian}`);
    } else {
        emptyCount++;
        console.log(`${report}: ❌ empty`);
    }
}

console.log(`\nTotal: ${reports.length} | OK: ${okCount} | Empty: ${emptyCount}`);
