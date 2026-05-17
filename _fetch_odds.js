const https = require('https');

const url = 'https://cp.zgzcw.com/lottery/jcplayvsForJsp.action?lotteryId=23&issue=20260512';

const req = https.request(url, {
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        // 看有没有赔率相关字段
        const lines = d.split('\n').filter(l => 
            l.includes('sp') || l.includes('odds') || 
            l.includes('胜') || l.includes('平') || l.includes('负') ||
            l.includes('欧赔') || l.includes('handicap')
        );
        console.log('赔率相关行 (前20行):\n');
        lines.slice(0, 20).forEach(l => console.log(l.substring(0, 200)));
        
        // 也看看 tr 行的结构
        const trLines = d.split('\n').filter(l => l.includes('mN='));
        console.log('\n\ntr行结构 (前5行):\n');
        trLines.slice(0, 5).forEach(l => console.log(l.substring(0, 300)));
    });
});
req.on('error', e => console.error(e));
req.on('timeout', () => { req.destroy(); console.log('TIMEOUT'); });
req.end();
