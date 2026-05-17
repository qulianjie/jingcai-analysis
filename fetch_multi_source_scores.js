const https = require('https');
const fs = require('fs');
const path = require('path');

// 尝试不同的zgzcw.com API端点获取历史比分
async function fetchScores() {
    const urls = [
        // 标准开奖结果
        'https://cp.zgzcw.com/dc/getKaijiangFootBall.action',
        // 带日期参数
        'https://cp.zgzcw.com/dc/getKaijiangFootBall.action?date=2026-05-09',
        'https://cp.zgzcw.com/dc/getKaijiangFootBall.action?date=2026-05-08',
        'https://cp.zgzcw.com/dc/getKaijiangFootBall.action?date=2026-05-07',
        // 竞彩开奖
        'https://cp.zgzcw.com/jc/kaipan/',
        // 500.com 开奖
        'https://trade.500.com/jcgc/',
        // 竞彩网
        'https://www.sporttery.cn/jc/jszq/jczqxq/jcqfjj.html',
    ];
    
    const results = {};
    
    for (const url of urls) {
        try {
            console.log(`\n获取: ${url}`);
            const html = await fetchUrl(url);
            
            // 解析比分
            const rows = html.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
            let found = 0;
            
            for (const row of rows) {
                const numMatch = row.match(/(周[一二三四五六日]\d+)/);
                if (!numMatch) continue;
                const matchNum = numMatch[1];
                
                const scoreMatch = row.match(/(\d{1,2})[：:](\d{1,2})\s*\(\d{1,2}[：:]\d{1,2}\)/);
                if (!scoreMatch) continue;
                
                const homeScore = parseInt(scoreMatch[1]);
                const awayScore = parseInt(scoreMatch[2]);
                results[matchNum] = `${homeScore}:${awayScore}`;
                found++;
            }
            
            console.log(`  找到 ${found} 场比分`);
        } catch (e) {
            console.log(`  错误: ${e.message}`);
        }
    }
    
    return results;
}

function fetchUrl(url) {
    return new Promise((resolve) => {
        const req = https.request(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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

async function main() {
    console.log('从多个源获取比分...\n');
    const scores = await fetchScores();
    
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
}

main().catch(console.error);
