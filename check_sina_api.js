const https = require('https');
const req = https.request({
    hostname: 'lottery.sina.com.cn',
    path: '/kaijiang/detail.shtml?game=301&gameTypes=spf&date=2026-05-06',
    headers: { 'User-Agent': 'Mozilla/5.0' }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Length:', d.length);
        // Find script sources
        const scripts = d.match(/<script[^>]*src="([^"]+)"/g);
        if (scripts) console.log('Scripts:', scripts.length);
        // Find API endpoints
        const apis = d.match(/https?:\/\/[^"'\s]+api[^"'\s]*/gi);
        if (apis) console.log('APIs:', apis.slice(0, 10));
        // Find any fetch/axios calls
        const fetches = d.match(/fetch\(['"](https?:\/\/[^'"]+)['"]/g);
        if (fetches) console.log('Fetches:', fetches.slice(0, 10));
        // Look for data URLs
        const dataUrls = d.match(/https?:\/\/[^"'\s]+kaijiang[^"'\s]*/gi);
        if (dataUrls) console.log('Data URLs:', dataUrls.slice(0, 10));
        // Print first 2000 chars
        console.log('\n--- HTML Preview ---');
        console.log(d.substring(0, 2000));
    });
});
req.on('error', e => console.log('Error:', e.message));
req.end();
