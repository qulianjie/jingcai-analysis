const fs = require('fs');
const path = require('path');

// 从本地任务文件中提取竞彩欧赔数据
function extractOddsFromLocalFiles(dateStr) {
    const odds = {};
    const taskDir = path.join(__dirname, 'tasks', dateStr);
    
    if (!fs.existsSync(taskDir)) {
        console.log('[本地] 任务目录不存在');
        return odds;
    }
    
    const files = fs.readdirSync(taskDir).filter(f => f.endsWith('.md') && !f.startsWith('sunday'));
    console.log(`[本地] 找到 ${files.length} 个报告文件`);
    
    for (const file of files) {
        try {
            const content = fs.readFileSync(path.join(taskDir, file), 'utf8');
            
            // 提取竞彩编号: "周一001"
            const numMatch = file.match(/^([\u5468][\u4E00-\u516D\u65E5]\d+)[_]/);
            if (!numMatch) continue;
            const matchNum = numMatch[1];
            
            // 从报告中提取竞彩官方欧赔（即时赔率）
            // 格式: | 竞彩官方 | 1.95 | 3.62 | 2.94 | 1.95 | 3.53 | 3.00 | ➡⬇⬆ |
            const lines = content.split('\n');
            for (const line of lines) {
                if (line.includes('竞彩官方') && line.includes('|')) {
                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                    // parts: ['竞彩官方', '1.95', '3.62', '2.94', '1.95', '3.53', '3.00', '➡⬇⬆']
                    if (parts.length >= 7) {
                        odds[matchNum] = {
                            win: parseFloat(parts[4]),  // 即时胜
                            draw: parseFloat(parts[5]),  // 即时平
                            loss: parseFloat(parts[6])   // 即时负
                        };
                        break;
                    }
                }
            }
        } catch (e) {}
    }
    
    console.log(`[本地] 提取到 ${Object.keys(odds).length} 场欧赔`);
    return odds;
}

// 测试
const dateStr = '2026-05-11';
const odds = extractOddsFromLocalFiles(dateStr);
console.log('\n全部:');
Object.keys(odds).forEach(k => {
    console.log(`  ${k}: ${odds[k].win} / ${odds[k].draw} / ${odds[k].loss}`);
});
