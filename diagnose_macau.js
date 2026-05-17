// 诊断澳门亚盘字段为什么为空
const fs = require('fs');
const path = require('path');

const dataDir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15/data';
const tasksDir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15';

const matchDirs = fs.readdirSync(dataDir).filter(d => d.startsWith('match'));
const reports = fs.readdirSync(tasksDir).filter(f => f.endsWith('.md') && f !== 'sunday_matches.md');

console.log(`\n=== 检查 2026-05-15 澳门亚盘数据 ===\n`);

for (const dir of matchDirs) {
    const metaPath = path.join(dataDir, dir, 'meta.json');
    const g3Dir = path.join(dataDir, dir, 'group03_asian');
    const step6Path = path.join(g3Dir, 'step6_asian_base.txt');
    
    let macau_line = '';
    let step6_has_macau = false;
    
    if (fs.existsSync(metaPath)) {
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        macau_line = meta.macau_line || '';
    }
    
    if (fs.existsSync(step6Path)) {
        const c6 = fs.readFileSync(step6Path, 'utf8');
        step6_has_macau = c6.includes('澳门') && c6.includes('|');
    }
    
    // Find matching report
    const report = reports.find(r => r.includes(dir.replace('match', '')) || dir.includes(r.split('_')[0]?.replace(/周[^_]*/, '')));
    
    const matchNum = matchDirs.indexOf(dir) + 1;
    console.log(`match${String(matchNum).padStart(2,'0')} (${dir}):`);
    console.log(`  meta.json macau_line: "${macau_line}"`);
    console.log(`  step6 has 澳门: ${step6_has_macau}`);
}

console.log(`\n=== 检查报告中的"澳门亚盘"汇总行 ===\n`);

for (const report of reports.slice(0, 5)) {
    const content = fs.readFileSync(path.join(tasksDir, report), 'utf8');
    
    // 查找结论部分的汇总表格
    const conclusionSection = content.match(/# [^#\n\r]+[\s\S]*?(?=# [^#\r\n]|$)/);
    if (conclusionSection) {
        const macauMatch = conclusionSection[0].match(/\|\s*澳门亚盘\s*\|\s*([^|]+)\|\s*([^|]+)\|/);
        console.log(`${report}:`);
        console.log(`  报告结论中的澳门亚盘: ${macauMatch ? `"${macauMatch[1].trim()} | ${macauMatch[2].trim()}"` : 'NOT FOUND'}`);
    }
    
    // 检查报告全文
    const allMatches = content.match(/\|\s*澳门亚盘\s*\|\s*([^|]+)\|\s*([^|]+)\|/g);
    if (allMatches) {
        console.log(`  全文中的澳门亚盘行: ${allMatches.length} 处`);
        allMatches.slice(0, 2).forEach(m => console.log(`    ${m.trim()}`));
    } else {
        console.log(`  全文中的澳门亚盘行: 0 处`);
    }
    
    // 检查各维度信号明细表
    const signalTable = content.match(/\|[^|]*亚盘[^|]*\|[^|]*\|[^|]*\|/g);
    if (signalTable) {
        console.log(`  含"亚盘"的表行: ${signalTable.length}`);
        signalTable.slice(0, 3).forEach(m => console.log(`    ${m.trim()}`));
    }
    console.log('');
}
