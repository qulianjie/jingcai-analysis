const https = require('https');

// 正确的比分提取方案
// 问题: 500.com移动端有EdgeOne反爬，需要处理cookie
// 解决: 使用 zgzcw API (无需反爬)

async function fetchScores() {
    return new Promise((resolve) => {
        const req = https.request({
            hostname: 'cp.zgzcw.com',
            path: '/dc/getKaijiangFootBall.action',
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://cp.zgzcw.com/jczq/kaijiang/'
            },
            timeout: 15000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    // 解析HTML表格
                    const rows = d.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
                    const scores = {};
                    
                    for (const row of rows) {
                        // 提取竞彩编号
                        const numMatch = row.match(/(周[一二三四五六日]\d+)/);
                        if (!numMatch) continue;
                        
                        let matchNum = numMatch[1];
                        const dayMatch = matchNum.match(/(周[一二三四五六日])(\d+)/);
                        if (dayMatch && dayMatch[2].length < 3) {
                            matchNum = dayMatch[1] + dayMatch[2].padStart(3, '0');
                        }
                        
                        // 提取比分 - 格式: "0:1 (0:0)" 取第一个
                        const scoreMatch = row.match(/(\d{1,2})[：:](\d{1,2})\s*\(/);
                        if (!scoreMatch) continue;
                        
                        const home = parseInt(scoreMatch[1]);
                        const away = parseInt(scoreMatch[2]);
                        
                        // 过滤时间格式（如 22:45）
                        if (home > 15 || away > 15) continue;
                        
                        scores[matchNum] = { homeScore: home, awayScore: away };
                    }
                    
                    console.log(`获取到 ${Object.keys(scores).length} 场比分`);
                    for (const [k, v] of Object.entries(scores).sort()) {
                        console.log(`  ${k}: ${v.homeScore}:${v.awayScore}`);
                    }
                    
                    resolve(scores);
                } catch (e) {
                    console.log('Parse error:', e.message);
                    resolve({});
                }
            });
        });
        
        req.on('error', () => resolve({}));
        req.on('timeout', () => { req.destroy(); resolve({}); });
        req.end();
    });
}

fetchScores().then(scores => {
    console.log('\n完成');
});
