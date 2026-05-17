const https = require('https');

// 尝试从 vipc.cn 获取开奖结果
const req = https.request({
    hostname: 'www.vipc.cn',
    path: '/results/jczq',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml'
    },
    timeout: 15000,
    followRedirect: true,
    maxRedirects: 5
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Length:', d.length);
        console.log('Content:', d.slice(0, 5000));
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
