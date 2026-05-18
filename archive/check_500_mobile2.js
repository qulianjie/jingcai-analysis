const https = require('https');
const fs = require('fs');

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
        fs.writeFileSync('c:/temp/500_mobile_raw.txt', d, 'utf8');
        console.log('Status:', res.statusCode);
        console.log('Headers:', JSON.stringify(res.headers));
        console.log('\nHTML content:');
        console.log(d.slice(0, 2000));
    });
});

req.on('error', e => console.log('Error:', e.message));
req.end();
