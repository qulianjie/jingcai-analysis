const https = require('https');

// 从新浪彩票页面源码中找数据接口
const req = https.request({
    hostname: 'lottery.sina.com.cn',
    path: '/kaijiang/detail.shtml?game=301&gameTypes=spf&date=2026-05-10',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    timeout: 15000
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        // 保存完整HTML
        const fs = require('fs');
        fs.writeFileSync('c:/temp/sina_lottery.html', d, 'utf8');
        
        // 找所有script引用
        const scripts = d.match(/src="([^"]+)"/g) || [];
        console.log('=== JS files ===');
        scripts.forEach(s => console.log('  ', s));
        
        // 找所有URL
        const urls = d.match(/https?:\/\/[^"'\s<>]+\.(?:php|json|do|action|api)[^"'\s<>]*/gi) || [];
        console.log('\n=== Data URLs ===');
        urls.forEach(u => console.log('  ', u));
        
        // 找AJAX调用
        const ajax = d.match(/ajax|fetch|getJSON|\.get\(|\.post\(|XMLHttpRequest/gi) || [];
        console.log('\n=== AJAX calls found:', ajax.length);
        
        // 找包含kaijiang或result的变量
        const vars = d.match(/var\s+\w*(kaijiang|result|match|score)\w*\s*=/gi) || [];
        console.log('\n=== Result variables ===');
        vars.forEach(v => console.log('  ', v));
        
        // 找data属性
        const data = d.match(/data-\w+="[^"]+"/g) || [];
        console.log('\n=== Data attributes ===');
        data.forEach(d => console.log('  ', d));
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
