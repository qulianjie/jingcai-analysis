const https = require('https');

async function main() {
    console.log('=== 调试赛果匹配问题 ===\n');
    
    // 1. 获取赛果
    const results = {};
    const dateStr = '2026-05-10';
    
    // 从 500.com 获取
    const html = await new Promise((resolve) => {
        const req = https.request({
            hostname: 'trade.500.com',
            path: '/jczq/jczqlc.php?playid=270&date=' + dateStr,
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://trade.500.com/jczq/'
            },
            timeout: 15000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(d));
        });
        req.on('error', () => resolve(''));
        req.end();
    });
    
    console.log('HTML length:', html.length);
    
    // 提取所有 "周日XX" 格式
    const allMatches = html.match(/周[一二三四五六日]\d+/g) || [];
    console.log('\n所有周X格式:', allMatches.slice(0, 20));
    
    // 提取 tr 行
    const rows = html.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
    console.log('\nTr rows:', rows.length);
    
    for (let i = 0; i < Math.min(rows.length, 5); i++) {
        console.log('\nRow', i, ':', rows[i].slice(0, 300));
    }
}

main().catch(err => console.error(err));
