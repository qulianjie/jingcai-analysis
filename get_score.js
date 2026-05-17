const https = require('https');

// 从500.com获取比分
const req = https.request({
    hostname: 'odds.500.com',
    path: '/schj.shtml',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
}, res => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Length:', body.length);
        // 查找比分表格
        const scores = body.match(/<td[^>]*>(\d+):(\d+)<\/td>/g);
        if (scores) {
            console.log('Scores found:', scores.length);
            scores.forEach(s => console.log(s));
        }
        // 查找5-07的比赛
        const matches = body.match(/2026-05-07[\s\S]{0,500}/g);
        if (matches) {
            console.log('5-07 matches:', matches.length);
            matches.forEach(m => console.log(m.substring(0, 200)));
        }
        console.log('First 500:', body.substring(0, 500));
    });
});
req.end();
