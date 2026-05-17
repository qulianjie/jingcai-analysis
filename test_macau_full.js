// Test: simulate the full extractMatchInfo flow for 05-15 reports
const fs = require('fs');
const path = require('path');

const tasksDir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15';
const reports = fs.readdirSync(tasksDir).filter(f => f.endsWith('.md') && f !== 'sunday_matches.md');

for (const report of reports.slice(0, 3)) {
    const reportPath = path.join(tasksDir, report);
    const content = fs.readFileSync(reportPath, 'utf8');
    
    // Simulate extractScoreFromTable for 澳门亚盘
    function extractScoreFromTable(text, label) {
        if (label === '澳门亚盘') {
            const conclusionSection = text.match(/# [\u4e5d9][\u90e8\u9879\u5206\u7ae0][\s\S]*?(?=# [^\u4e5d9]|$)/);
            if (conclusionSection) {
                const m = conclusionSection[0].match(/\|\s*澳门亚盘\s*\|\s*([^|]+)\|\s*([^|]+)\|/);
                if (m) return m[1].trim() + ' | ' + m[2].trim();
            }
            const trendM = text.match(/\|\s*澳门亚盘\s*\|\s*([+-][\d.]+\s+利好[主客])\s*\|\s*([\d.]+%)\s*\|/);
            if (trendM) return trendM[1].trim() + ' | ' + trendM[2].trim();
            return '';
        }
        return '';
    }
    
    const macau_asian = extractScoreFromTable(content, '澳门亚盘');
    console.log(`${report}: macau_asian = "${macau_asian || '(empty)'}"`);
}
