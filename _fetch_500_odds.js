const https = require('https');

// 尝试从 500.com 获取竞彩欧赔数据
const url = 'https://trade.500.com/jc odds.php?date=2026-05-12';

const req = https.request(url, {
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Length:', d.length);
        if (d.length > 0) {
            console.log('First 500 chars:', d.substring(0, 500));
        }
    });
});
req.on('error', e => console.error(e));
req.on('timeout', () => { req.destroy(); console.log('TIMEOUT'); });
req.end();
