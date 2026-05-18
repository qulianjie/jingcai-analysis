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
        
        // 显示第3行（第一个数据行）的完整内容
        if (rows[3]) {
            console.log('=== Row 3 (first data row) ===');
            console.log(rows[3].slice(0, 1000));
        }
        
        // 尝试用不同方式提取比分
        console.log('\n=== Trying to extract scores ===');
        
        // 提取所有 td 内容
        const allTd = d.match(/<td[^>]*>(.*?)<\/td>/gs) || [];
        console.log('Total td cells:', allTd.length);
        
        // 从第12个 td 开始（跳过表头）
        for (let i = 12; i < Math.min(allTd.length, 60); i++) {
            const cell = allTd[i].replace(/<[^>]*>/g, '').trim();
            if (cell) console.log('td[' + i + ']:', cell);
        }
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
