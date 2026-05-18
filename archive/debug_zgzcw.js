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
        // 提取所有 tr 行
        const rows = d.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
        console.log('Total tr rows:', rows.length);
        
        // 查找包含 "周日" 的行
        for (const row of rows) {
            const numMatch = row.match(/(周[一二三四五六日]\d+)/);
            if (numMatch && numMatch[1].startsWith('周日')) {
                const scoreMatch = row.match(/(\d{1,2})[：:](\d{1,2})/);
                console.log(numMatch[1], scoreMatch ? scoreMatch[0] : 'no score');
            }
        }
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
