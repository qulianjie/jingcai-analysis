const https = require('https');
const fs = require('fs');
const path = require('path');

// 解析HTML表格获取比分
function parseScores(html) {
    const scores = {};
    const rows = html.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
    
    for (const row of rows) {
        const numMatch = row.match(/(周[一二三四五六日]\d+)/);
        if (!numMatch) continue;
        const matchNum = numMatch[1];
        
        // 匹配比分格式: 1:0 (0:0)
        const scoreMatch = row.match(/(\d{1,2})[：:](\d{1,2})\s*\(\d{1,2}[：:]\d{1,2}\)/);
        if (!scoreMatch) continue;
        
        const homeScore = parseInt(scoreMatch[1]);
        const awayScore = parseInt(scoreMatch[2]);
        scores[matchNum] = `${homeScore}:${awayScore}`;
    }
    
    return scores;
}

// 获取指定日期的比分
function fetchScoresByDate(dateStr) {
    return new Promise((resolve) => {
        // zgzcw.com的日期格式
        const url = `/dc/getKaijiangFootBall.action?date=${dateStr}`;
        
        const req = https.request({
            hostname: 'cp.zgzcw.com',
            path: url,
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://cp.zgzcw.com/'
            },
            timeout: 10000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                const scores = parseScores(d);
                resolve(scores);
            });
        });
        req.on('error', () => resolve({}));
        req.on('timeout', () => { req.destroy(); resolve({}); });
        req.end();
    });
}

// 获取所有日期的比分（zgzcw.com可能只返回最近13天，但值得一试）
async function fetchAllDates() {
    const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
    const dates = fs.readdirSync(BASE).filter(d => {
        const dp = path.join(BASE, d);
        return fs.statSync(dp).isDirectory() && /^\d{4}-\d{2}-\d{2}$/.test(d);
    }).sort();
    
    console.log(`需要获取 ${dates.length} 个日期的比分\n`);
    
    const allScores = {};
    
    // 分批获取，避免太快被ban
    for (let i = 0; i < dates.length; i++) {
        const date = dates[i];
        const scores = await fetchScoresByDate(date);
        
        if (Object.keys(scores).length > 0) {
            console.log(`${date}: ${Object.keys(scores).length}场`);
            Object.assign(allScores, scores);
        } else {
            // 尝试不同格式
            const formatted = date.replace(/-/g, '');
            const scores2 = await fetchScoresByDate(formatted);
            if (Object.keys(scores2).length > 0) {
                console.log(`${date} (${formatted}): ${Object.keys(scores2).length}场`);
                Object.assign(allScores, scores2);
            }
        }
        
        // 每5个请求停顿1秒
        if ((i + 1) % 5 === 0) {
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    
    return allScores;
}

async function main() {
    console.log('逐日获取比分...\n');
    const scores = await fetchAllDates();
    
    console.log(`\n总唯一比分: ${Object.keys(scores).length}场`);
    for (const [k, v] of Object.entries(scores).sort()) {
        console.log(`  ${k}: ${v}`);
    }
    
    // 写入meta.json
    const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
    let updated = 0;
    
    for (const d of fs.readdirSync(BASE).sort()) {
        const dp = path.join(BASE, d);
        if (!fs.statSync(dp).isDirectory()) continue;
        const dataDir = path.join(dp, 'data');
        if (!fs.existsSync(dataDir)) continue;
        
        let dateUpdated = 0;
        for (const m of fs.readdirSync(dataDir).sort()) {
            if (!m.startsWith('match')) continue;
            const metaPath = path.join(dataDir, m, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const matchnum = meta.matchnum || '';
            
            if (scores[matchnum]) {
                meta.score = scores[matchnum];
                fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
                updated++;
                dateUpdated++;
            }
        }
        if (dateUpdated > 0) console.log(`  ${d}: 更新${dateUpdated}场`);
    }
    
    console.log(`\n总更新: ${updated}场`);
    
    // 重新跑分析
    console.log('\n重新跑组合分析...\n');
}

main().catch(console.error);
