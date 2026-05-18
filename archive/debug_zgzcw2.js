const https = require('https');

const req = https.request({
    hostname: 'cp.zgzcw.com',
    path: '/dc/getKaijiangFootBall.action',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const rows = d.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
        console.log('Total tr rows:', rows.length);
        
        // 显示前3行的完整内容
        for (let i = 0; i < Math.min(rows.length, 3); i++) {
            console.log('\n=== Row', i, '===');
            console.log(rows[i].slice(0, 500));
        }
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
