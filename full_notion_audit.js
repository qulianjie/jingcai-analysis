const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

function queryNotionByDate(dateStr) {
    const data = JSON.stringify({
        filter: { and: [
            { property: '比赛日期', date: { on_or_after: dateStr } },
            { property: '比赛日期', date: { on_or_before: dateStr } }
        ]},
        page_size: 100
    });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { try { resolve(JSON.parse(b)); } catch(e) { reject(e); } }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

function trunc1(v) {
    if (!v || isNaN(v)) return 0;
    return Math.floor(v * 10) / 10;
}

async function main() {
    const results = [];
    
    for (let d = 1; d <= 11; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const dateDir = path.join(tasksDir, dateStr, 'data');
        
        // Get local data
        let localCount = 0;
        const localMatches = {};
        if (fs.existsSync(dateDir)) {
            const dirs = fs.readdirSync(dateDir).filter(x => x.startsWith('match'));
            localCount = dirs.length;
            for (const dir of dirs) {
                const mp = path.join(dateDir, dir, 'meta.json');
                if (fs.existsSync(mp)) {
                    const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
                    if (m.matchnum) localMatches[m.matchnum] = path.join(dateDir, dir);
                }
            }
        }
        
        // Get Notion data
        const notionResult = await queryNotionByDate(dateStr);
        const notionPages = (notionResult.results || []).filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        
        console.log('\n=== ' + dateStr + ' ===');
        console.log('Notion=' + notionPages.length + ', 本地=' + localCount);
        
        // Check each Notion page
        for (const page of notionPages) {
            const name = page.properties.Name?.title?.[0]?.plain_text || '';
            const matchCol = page.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            const dateCol = page.properties['比赛日期']?.date?.start || '';
            
            const rqWin = page.properties['让球指数胜']?.number;
            const rqDraw = page.properties['让球指数平']?.number;
            const rqLoss = page.properties['让球指数负']?.number;
            const rqWinEnd = page.properties['终盘让球指数胜']?.number;
            const rqDrawEnd = page.properties['终盘让球指数平']?.number;
            const rqLossEnd = page.properties['终盘让球指数负']?.number;
            const ma = page.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            const maEnd = page.properties['终盘竞彩澳门亚盘']?.rich_text?.[0]?.plain_text || '';
            
            // Extract matchnum from Name
            const mnMatch = name.match(/^([周][一二三四五六日]\d+)/);
            const mn = mnMatch ? mnMatch[1] : '';
            
            // Check match column starts with 周
            const matchColOk = matchCol.startsWith('周');
            
            // Check duplicates
            // Check if matchnum exists in local
            const hasLocal = !!localMatches[mn];
            
            // Build status
            const issues = [];
            if (!matchColOk) issues.push('比赛列不以周开头');
            if (dateCol !== dateStr) issues.push('日期不匹配(' + dateCol + ')');
            if (!hasLocal && mn) issues.push('本地无此记录');
            
            if (issues.length > 0) {
                console.log('  ⚠️ ' + matchCol + ' | ' + name.slice(0, 40) + ' | ' + issues.join('; '));
            }
            
            results.push({
                date: dateStr,
                mn,
                name,
                matchCol,
                dateCol,
                rqWin, rqDraw, rqLoss,
                rqWinEnd, rqDrawEnd, rqLossEnd,
                ma, maEnd,
                issues,
                pageId: page.id
            });
        }
    }
    
    // Summary
    console.log('\n=== 汇总 ===');
    const totalNotion = results.length;
    const withMatchColIssue = results.filter(r => r.issues.some(i => i.includes('比赛列'))).length;
    const withDateIssue = results.filter(r => r.issues.some(i => i.includes('日期'))).length;
    const withLocalIssue = results.filter(r => r.issues.some(i => i.includes('本地'))).length;
    const totalIssues = results.filter(r => r.issues.length > 0).length;
    
    console.log('总记录: ' + totalNotion);
    console.log('比赛列问题: ' + withMatchColIssue);
    console.log('日期问题: ' + withDateIssue);
    console.log('本地无此记录: ' + withLocalIssue);
    console.log('有问题的记录: ' + totalIssues);
    
    if (totalIssues > 0) {
        console.log('\n问题详情:');
        for (const r of results) {
            if (r.issues.length > 0) {
                console.log('  ' + r.date + ' | ' + r.mn + ' | ' + r.name.slice(0, 40) + ' | ' + r.issues.join('; '));
            }
        }
    }
}

main().catch(e => console.error(e));
