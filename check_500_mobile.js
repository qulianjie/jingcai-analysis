const https = require('https');

const req = https.request({
    hostname: 'live.m.500.com',
    path: '/home/zq/jczq/2026-05-10',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        // 保存完整HTML
        const fs = require('fs');
        fs.writeFileSync('c:/temp/500_mobile.html', d, 'utf8');
        console.log('HTML length:', d.length);
        
        // 提取所有周日XX的比赛段
        const sections = d.match(/(周[一二三四五六日]\d+)[\s\S]*?完场/g) || [];
        console.log('\n找到', sections.length, '场比赛\n');
        
        for (const section of sections) {
            const numMatch = section.match(/(周[一二三四五六日]\d+)/);
            if (!numMatch) continue;
            const matchNum = numMatch[1];
            
            // 提取比分 - 找"完场"前的数字模式
            // 格式可能是: "完场 1:0" 或 "完场 2:1"
            const scoreMatch = section.match(/完场\s*(\d+)[：:](\d+)/);
            if (scoreMatch) {
                console.log(`${matchNum}: ${scoreMatch[1]}:${scoreMatch[2]}`);
            } else {
                // 尝试其他格式
                const allNums = section.match(/\d+/g) || [];
                console.log(`${matchNum}: 未找到标准比分，数字: ${allNums.slice(-6).join(', ')}`);
            }
        }
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
