const https = require('https');
const fs = require('fs');

// 从 live.500.com 获取 5月10日 竞彩足球比分
// 这个页面用 AJAX 加载数据，我们需要找到 AJAX 接口

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
        
        // 查找 AJAX 接口
        // 搜索 js 文件引用或 AJAX URL
        const ajaxUrls = text.match(/https?:\/\/[^"'\s]*ajax[^"'\s]*/gi) || [];
        const jsFiles = text.match(/src="([^"]+\.js)"/g) || [];
        const dataUrls = text.match(/https?:\/\/[^"'\s]*data[^"'\s]*/gi) || [];
        const scoreUrls = text.match(/https?:\/\/[^"'\s]*(score|result|match)[^"'\s]*/gi) || [];
        
        console.log('=== AJAX URLs ===');
        ajaxUrls.forEach(u => console.log('  ', u));
        
        console.log('\n=== JS Files ===');
        jsFiles.slice(0, 10).forEach(u => console.log('  ', u));
        
        console.log('\n=== Data URLs ===');
        dataUrls.forEach(u => console.log('  ', u));
        
        console.log('\n=== Score URLs ===');
        scoreUrls.forEach(u => console.log('  ', u));
        
        // 搜索包含 "api" 或 "interface" 的 URL
        const apiUrls = text.match(/https?:\/\/[^"'\s]*api[^"'\s]*/gi) || [];
        console.log('\n=== API URLs ===');
        apiUrls.forEach(u => console.log('  ', u));
        
        // 搜索包含 "zx" (最新) 或 "fc" (足球) 的路径
        const zxUrls = text.match(/\/\/[^"'\s]*zx[^"'\s]*/gi) || [];
        const fcUrls = text.match(/\/\/[^"'\s]*fc[^"'\s]*/gi) || [];
        console.log('\n=== ZX URLs ===');
        zxUrls.forEach(u => console.log('  ', u));
        console.log('\n=== FC URLs ===');
        fcUrls.forEach(u => console.log('  ', u));
        
        // 搜索 script 标签中的变量
        const scripts = text.match(/<script[^>]*>([\s\S]*?)<\/script>/gi) || [];
        for (const script of scripts) {
            // 找包含 "e=" 或 "date" 或 "match" 的变量
            if (script.includes('e=') || script.includes('date') || script.includes('match')) {
                const clean = script.replace(/<[^>]*>/g, '').trim();
                if (clean.length > 10 && clean.length < 500) {
                    console.log('\n=== Script snippet ===');
                    console.log(clean.slice(0, 300));
                }
            }
        }
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
