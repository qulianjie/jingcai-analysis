const https = require('https');

// 尝试lotto.sina.cn的API
const apis = [
    // 竞彩足球开奖API
    'https://lotto.sina.com.cn/api/lottery/kaijiang/detail?game=301&gameTypes=spf&date=2026-05-10',
    'https://lotto.sina.com.cn/api/lottery/kaijiang/detail?game=301&gameTypes=spf&date=2026-05-10&callback=?',
    'https://api.sporttery.cn/api/kaijiang/detail?game=301&gameTypes=spf&date=2026-05-10',
    // lotto.sina.cn 移动端
    'https://lotto.sina.cn/open/openDetailJc.d.html?lottId=301&gameTypes=spf',
];

let completed = 0;
for (const url of apis) {
    const u = new URL(url);
    const req = https.request({
        hostname: u.hostname,
        path: u.pathname + u.search,
        method: 'GET',
        headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://lottery.sina.com.cn/kaijiang/detail.shtml?game=301'
        },
        timeout: 10000
    }, res => {
        let d = '';
        res.on('data', c => d += c);
        res.on('end', () => {
            completed++;
            console.log(`\n[${url}] status: ${res.statusCode} len: ${d.length}`);
            if (d.length > 0 && d.length < 10000) {
                console.log('Content:', d.slice(0, 2000));
            } else if (d.length > 0) {
                console.log('Content:', d.slice(0, 500));
            }
        });
    });
    req.on('error', e => {
        console.log(`[${url}] error: ${e.message}`);
        completed++;
    });
    req.end();
}
