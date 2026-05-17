const https = require('https');
const fs = require('fs');

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
    const chunks = [];
    res.on('data', c => chunks.push(c));
    res.on('end', () => {
        const buf = Buffer.concat(chunks);
        const text = require('iconv-lite').decode(buf, 'gbk');
        
        // 保存完整 HTML 到文件
        fs.writeFileSync('c:/temp/500_full.html', text, 'utf8');
        console.log('Saved full HTML to c:/temp/500_full.html');
        console.log('HTML length:', text.length);
        
        // 提取所有 tr 行
        const rows = text.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
        console.log('\n=== Total tr rows:', rows.length, '===');
        
        // 找包含比分的 td
        // 比分通常在 <td> 里，格式如 "1:0" 或 "0:0"
        // 让我先看看每个 tr 的结构
        
        for (let i = 0; i < Math.min(rows.length, 5); i++) {
            console.log('\n=== Row', i, '===');
            console.log(rows[i].slice(0, 500));
        }
        
        // 提取所有 td 内容
        const allTd = text.match(/<td[^>]*>(.*?)<\/td>/gs) || [];
        console.log('\n=== Total td cells:', allTd.length, '===');
        
        // 找 "周日" 开头的 td 后面的比分
        const results = {};
        for (let i = 0; i < allTd.length; i++) {
            const td = allTd[i];
            const clean = td.replace(/<[^>]*>/g, '').trim();
            
            // 找 "周日XXX" 
            const matchNum = clean.match(/(周[一二三四五六日]\d+)/);
            if (matchNum) {
                // 往后找比分（通常在后面几个 td 里）
                for (let j = i + 1; j < Math.min(i + 10, allTd.length); j++) {
                    const scoreTd = allTd[j].replace(/<[^>]*>/g, '').trim();
                    const scoreMatch = scoreTd.match(/^(\d{1,2}:\d{1,2})$/);
                    if (scoreMatch) {
                        let mn = matchNum[1];
                        const dayNum = mn.match(/(周[一二三四五六日])(\d+)/);
                        if (dayNum) {
                            mn = dayNum[1] + dayNum[2].padStart(3, '0');
                        }
                        results[mn] = scoreMatch[1];
                        break;
                    }
                }
            }
        }
        
        console.log('\n=== Extracted Scores ===');
        Object.keys(results).sort().forEach(k => {
            console.log(`  ${k}: ${results[k]}`);
        });
        console.log(`\nTotal: ${Object.keys(results).length} scores extracted`);
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
