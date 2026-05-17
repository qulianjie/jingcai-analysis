const https = require('https');

const url = 'https://cp.zgzcw.com/lottery/jcplayvsForJsp.action?lotteryId=23&issue=20260511';

const req = https.request(url, {
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        // 查找包含赔率的 td 元素
        const tdMatches = d.match(/<td[^>]*class="[^"]*sp[^"]*"[^>]*>([^<]+)<\/td>/g);
        console.log('找到赔率 td:', tdMatches ? tdMatches.length : 0);
        if (tdMatches) {
            tdMatches.slice(0, 15).forEach((m, i) => console.log(`  ${i+1}: ${m.substring(0, 100)}`));
        }
        
        // 也看看 tr 的结构
        const trMatch = d.match(/<tr[^>]*mN="[^"]*"[^>]*>[\s\S]{0,500}<\/tr>/g);
        if (trMatch) {
            console.log('\n第一个比赛行:');
            console.log(trMatch[0].substring(0, 500));
        }
    });
});
req.on('error', e => console.error(e));
req.on('timeout', () => { req.destroy(); console.log('TIMEOUT'); });
req.end();
