const https = require('https');

const req = https.request({
    hostname: 'lottery.sina.com.cn',
    path: '/kaijiang/detail.shtml?game=301&gameTypes=spf&date=2026-05-10&0_ala_h5baidu&_headline=baidu_ala',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Length:', d.length);
        console.log('Content:', d.slice(0, 3000));
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
