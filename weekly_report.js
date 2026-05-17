const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = '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';
const DB_ID = '93490bfb-ac43-49be-a24d-9e3e5a225991';
const REPORTS_DIR = path.join(__dirname, '..', 'data', 'reports', 'jingcai');

if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

// ===== 查询 Notion 数据库 =====
function queryMatches(startDate, endDate) {
    const data = JSON.stringify({
        filter: {
            and: [
                {
                    property: '比赛日期',
                    date: { on_or_after: startDate }
                },
                {
                    property: '比赛日期',
                    date: { on_or_before: endDate }
                }
            ]
        },
        sorts: [
            { property: '比赛日期', direction: 'ascending' }
        ],
        page_size: 100
    });

    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${DB_ID}/query`,
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(d));
                } catch (e) {
                    reject(new Error(`Parse error: ${d}`));
                }
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

// ===== 生成周报 =====
async function generateWeeklyReport(weekOffset = 0) {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay() - 7 * weekOffset);
    startOfWeek.setHours(0, 0, 0, 0);
    
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    
    const startDate = startOfWeek.toISOString().split('T')[0];
    const endDate = endOfWeek.toISOString().split('T')[0];
    
    console.log(`\n📊 竞彩周报 - ${startDate} ~ ${endDate}\n`);
    
    // 查询数据
    const result = await queryMatches(startDate, endDate);
    const pages = result.results || [];
    
    // 统计
    const stats = {
        total: pages.length,
        withFeedback: 0,
        correct: 0,
        incorrect: 0,
        pending: 0,
        byLeague: {},
        byConfidence: { 高: { total: 0, correct: 0 }, 中: { total: 0, correct: 0 }, 低: { total: 0, correct: 0 } },
        matches: []
    };
    
    for (const page of pages) {
        const props = page.properties;
        
        const matchNum = props['竞彩编号']?.rich_text?.[0]?.plain_text || '';
        const date = props['比赛日期']?.date?.start || '';
        const league = props['联赛']?.rich_text?.[0]?.plain_text || '';
        const home = props['主队']?.rich_text?.[0]?.plain_text || '';
        const away = props['客队']?.rich_text?.[0]?.plain_text || '';
        const prediction = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
        const confidence = props['竞彩信心']?.select?.name || '';
        const actualScore = props['实际比分']?.rich_text?.[0]?.plain_text || '';
        const actualResult = props['实际结果']?.select?.name || '';
        const isCorrect = props['预测正确']?.checkbox;
        
        const match = { matchNum, date, league, home, away, prediction, confidence, actualScore, actualResult, isCorrect };
        stats.matches.push(match);
        
        // 按联赛统计
        if (league) {
            if (!stats.byLeague[league]) stats.byLeague[league] = { total: 0, correct: 0 };
            stats.byLeague[league].total++;
            if (isCorrect === true) stats.byLeague[league].correct++;
        }
        
        // 按信心统计
        if (confidence && stats.byConfidence[confidence]) {
            stats.byConfidence[confidence].total++;
            if (isCorrect === true) stats.byConfidence[confidence].correct++;
        }
        
        // 总体统计
        if (actualScore) {
            stats.withFeedback++;
            if (isCorrect === true) stats.correct++;
            else if (isCorrect === false) stats.incorrect++;
            else stats.pending++;
        }
    }
    
    // 计算准确率
    const accuracy = stats.withFeedback > 0 
        ? (stats.correct / stats.withFeedback * 100).toFixed(1) 
        : 'N/A';
    
    // 生成报告
    const report = `
# 📊 竞彩周报 - ${startDate} ~ ${endDate}

## 总体统计

| 指标 | 数值 |
|------|------|
| 比赛总数 | ${stats.total} |
| 已反馈 | ${stats.withFeedback} |
| 预测正确 | ${stats.correct} |
| 预测错误 | ${stats.incorrect} |
| 待查 | ${stats.pending} |
| **准确率** | **${accuracy}%** |

## 按联赛统计

${Object.entries(stats.byLeague).map(([league, s]) => 
    `| ${league} | ${s.total} | ${s.correct} | ${s.total > 0 ? (s.correct / s.total * 100).toFixed(1) : 0}% |`
).join('\n') || '| 无数据 | - | - | - |'}

## 按信心等级统计

| 信心 | 总数 | 正确 | 准确率 |
|------|------|------|--------|
| 高 | ${stats.byConfidence.高.total} | ${stats.byConfidence.高.correct} | ${stats.byConfidence.高.total > 0 ? (stats.byConfidence.高.correct / stats.byConfidence.高.total * 100).toFixed(1) : 0}% |
| 中 | ${stats.byConfidence.中.total} | ${stats.byConfidence.中.correct} | ${stats.byConfidence.中.total > 0 ? (stats.byConfidence.中.correct / stats.byConfidence.中.total * 100).toFixed(1) : 0}% |
| 低 | ${stats.byConfidence.低.total} | ${stats.byConfidence.低.correct} | ${stats.byConfidence.低.total > 0 ? (stats.byConfidence.低.correct / stats.byConfidence.低.total * 100).toFixed(1) : 0}% |

## 比赛明细

| 日期 | 编号 | 联赛 | 主队 | 客队 | 预测 | 信心 | 实际比分 | 结果 |
|------|------|------|------|------|------|------|----------|------|
${stats.matches.map(m => 
    `| ${m.date} | ${m.matchNum} | ${m.league} | ${m.home} | ${m.away} | ${m.prediction} | ${m.confidence} | ${m.actualScore || '-'} | ${m.isCorrect === true ? '✅' : m.isCorrect === false ? '❌' : '⏳'} |`
).join('\n') || '| 无数据 | - | - | - | - | - | - | - | - |'}

---
*报告生成时间: ${new Date().toISOString()}*
`;
    
    // 保存报告
    const reportFile = path.join(REPORTS_DIR, `weekly_${startDate}_${endDate}.md`);
    fs.writeFileSync(reportFile, report.trim(), 'utf8');
    
    console.log(`✅ 报告已保存: ${reportFile}`);
    console.log(`\n📈 本周准确率: ${accuracy}%`);
    console.log(`   总比赛: ${stats.total}, 已反馈: ${stats.withFeedback}`);
    
    return { stats, reportFile };
}

// ===== 主流程 =====
async function main() {
    const args = process.argv.slice(2);
    let weekOffset = 0;
    
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--week' && i + 1 < args.length) {
            weekOffset = parseInt(args[i + 1]) || 0;
        }
    }
    
    await generateWeeklyReport(weekOffset);
}

main().catch(err => {
    console.error('[FATAL]', err.message);
    process.exit(1);
});
