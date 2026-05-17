const https = require('https');
const fs = require('fs');

// 下载 live.500.com 的完整 HTML，然后提取 AJAX 接口
const req = https.request({
    hostname: 'live.500.com',
    path: '/?e=2026-05-10',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Encoding': 'identity'
    },
    timeout: 15000
}, res => {
    const chunks = [];
    res.on('data', c => chunks.push(c));
    res.on('end', () => {
        const buf = Buffer.concat(chunks);
        const text = require('iconv-lite').decode(buf, 'gbk');
        
        // 保存完整 HTML
        fs.writeFileSync('c:/temp/500_live.html', text, 'utf8');
        console.log('Saved HTML, length:', text.length);
        
        // 查找所有 URL 模式
        const urls = text.match(/https?:\/\/[^"'\s<>]+/gi) || [];
        const uniqueUrls = [...new Set(urls)];
        
        console.log('\n=== All unique URLs ===');
        uniqueUrls.forEach(u => console.log('  ', u));
        
        // 查找所有 script 中的变量和函数
        const scripts = text.match(/<script[^>]*>([\s\S]*?)<\/script>/gi) || [];
        for (const script of scripts) {
            const clean = script.replace(/<[^>]*>/g, '');
            // 找包含 url, ajax, get, post 的代码
            if (/url.*ajax|ajax.*url|\.get\(|\.post\(|fetch\(/i.test(clean)) {
                console.log('\n=== AJAX code ===');
                console.log(clean.slice(0, 500));
            }
            // 找包含 "e=" 或 "expect" 或 "match" 的代码
            if (/e\s*=\s*['"]?\d|expect|match.*info|game.*match/i.test(clean)) {
                console.log('\n=== Match code ===');
                console.log(clean.slice(0, 500));
            }
        }
        
        // 查找包含 "interface" 或 "ajax" 的文件引用
        const jsFiles = text.match(/src="([^"]+)"/g) || [];
        console.log('\n=== JS file references ===');
        jsFiles.forEach(f => console.log('  ', f));
        
        // 查找包含 "kaijiang" 或 "result" 或 "score" 的 URL
        const scoreUrls = text.match(/https?:\/\/[^"'\s]*(kaijiang|result|score|fc|zx)[^"'\s]*/gi) || [];
        console.log('\n=== Score-related URLs ===');
        scoreUrls.forEach(u => console.log('  ', u));
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
