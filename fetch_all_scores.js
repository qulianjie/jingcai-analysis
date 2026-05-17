const https = require('https');
const fs = require('fs');
const path = require('path');

// 从zgzcw.com获取开奖结果（支持指定日期）
function fetchScores(dateStr) {
    return new Promise((resolve) => {
        const url = dateStr ? 
            `/dc/getKaijiangFootBall.action?date=${dateStr}` :
            '/dc/getKaijiangFootBall.action';
        
        const req = https.request({
            hostname: 'cp.zgzcw.com',
            path: url,
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://cp.zgzcw.com/'
            },
            timeout: 15000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(d));
        });
        req.on('error', () => resolve(''));
        req.on('timeout', () => { req.destroy(); resolve(''); });
        req.end();
    });
}

// 解析比分HTML
function parseScores(html) {
    const scoreMap = {};
    const rows = html.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
    
    for (const row of rows) {
        const numMatch = row.match(/(周[一二三四五六日]\d+)/);
        if (!numMatch) continue;
        const matchNum = numMatch[1];
        
        const scoreMatch = row.match(/(\d{1,2})[：:](\d{1,2})\s*\(\d{1,2}[：:]\d{1,2}\)/);
        if (!scoreMatch) continue;
        
        const homeScore = parseInt(scoreMatch[1]);
        const awayScore = parseInt(scoreMatch[2]);
        scoreMap[matchNum] = `${homeScore}:${awayScore}`;
    }
    
    return scoreMap;
}

async function main() {
    console.log('从zgzcw.com获取开奖结果...\n');
    
    // 获取所有日期
    const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
    const dates = fs.readdirSync(BASE).filter(d => {
        const dp = path.join(BASE, d);
        return fs.statSync(dp).isDirectory();
    }).sort();
    
    console.log(`需要获取 ${dates.length} 个日期的比分`);
    
    // 尝试获取所有日期（zgzcw.com可能只返回最近13天）
    let totalScores = {};
    
    for (const date of dates) {
        // zgzcw.com的日期格式: 2026-05-09
        console.log(`获取 ${date}...`);
        const html = await fetchScores(date);
        const scores = parseScores(html);
        
        if (Object.keys(scores).length > 0) {
            console.log(`  ${date}: ${Object.keys(scores).length}场`);
            Object.assign(totalScores, scores);
        }
    }
    
    console.log(`\n获取到 ${Object.keys(totalScores).length} 场比分`);
    
    // 更新meta.json
    let updated = 0;
    
    for (const d of dates) {
        const dp = path.join(BASE, d);
        const dataDir = path.join(dp, 'data');
        if (!fs.existsSync(dataDir)) continue;
        
        let dateUpdated = 0;
        for (const m of fs.readdirSync(dataDir).sort()) {
            if (!m.startsWith('match')) continue;
            const metaPath = path.join(dataDir, m, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const matchnum = meta.matchnum || '';
            
            if (totalScores[matchnum]) {
                meta.score = totalScores[matchnum];
                fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
                updated++;
                dateUpdated++;
            }
        }
        if (dateUpdated > 0) console.log(`  ${d}: 更新${dateUpdated}场`);
    }
    
    console.log(`\n总更新: ${updated}场`);
}

main().catch(console.error);
