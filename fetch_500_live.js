const https = require('https');

// 从 live.500.com 获取 5月10日 竞彩足球开奖结果
const req = https.request({
    hostname: 'live.500.com',
    path: '/?e=2026-05-10',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html;charset=utf-8',
        'Accept-Encoding': 'identity'
    },
    timeout: 15000
}, res => {
    // 试试用 gbk 解码
    const chunks = [];
    res.on('data', c => chunks.push(c));
    res.on('end', () => {
        const buf = Buffer.concat(chunks);
        // 尝试用 gbk 解码
        try {
            const iconv = require('iconv-lite');
            const text = iconv.decode(buf, 'gbk');
            console.log('=== Using iconv-lite GBK ===');
            console.log('Title:', text.match(/<title>([^<]+)/)?.[1] || 'N/A');
            
            // 提取比分 - 找 "周X" + 比分
            const rows = text.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
            console.log('tr rows:', rows.length);
            
            // 提取所有 td 内容
            const allTd = [];
            const tdMatches = text.match(/<td[^>]*>(.*?)<\/td>/gs) || [];
            for (const td of tdMatches) {
                const clean = td.replace(/<[^>]*>/g, '').trim();
                if (clean) allTd.push(clean);
            }
            
            // 找 "周日" + 比分
            const sundayRows = text.match(/周日\d+.*?\d+:\d+/gs) || [];
            console.log('\n=== 周日X + 比分 ===');
            sundayRows.slice(0, 35).forEach(r => console.log(r));
            
        } catch (e) {
            console.log('iconv-lite not available, trying raw bytes');
            // 直接保存 HTML 到文件
            const fs = require('fs');
            fs.writeFileSync('c:/temp/500_raw.html', buf);
            console.log('Saved raw HTML to c:/temp/500_raw.html');
        }
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
