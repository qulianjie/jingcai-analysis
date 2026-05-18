const https = require('https');

async function main() {
    console.log('=== 调试赛果匹配问题 ===\n');
    
    const dateStr = '2026-05-10';
    const dateNum = dateStr.replace(/-/g, '');
    
    // 1. 尝试 sporttery API
    console.log('[1] sporttery API...');
    const sportteryData = await new Promise((resolve) => {
        const req = https.request({
            hostname: 'info.sporttery.cn',
            path: '/jc/match_result_v2.php?date=' + dateNum,
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout: 15000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(d));
        });
        req.on('error', e => resolve('ERROR: ' + e.message));
        req.on('timeout', () => { req.destroy(); resolve('TIMEOUT'); });
        req.end();
    });
    
    console.log('sporttery:', sportteryData.slice(0, 500));
    
    // 2. 尝试 zgzcw.com
    console.log('\n[2] zgzcw.com...');
    const zgzcwData = await new Promise((resolve) => {
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
            res.on('end', () => resolve(d));
        });
        req.on('error', e => resolve('ERROR: ' + e.message));
        req.on('timeout', () => { req.destroy(); resolve('TIMEOUT'); });
        req.end();
    });
    
    console.log('zgzcw length:', zgzcwData.length);
    if (zgzcwData.length > 100) {
        // 尝试解析 JSON
        try {
            const j = JSON.parse(zgzcwData);
            console.log('zgzcw JSON keys:', Object.keys(j));
            if (j.data && Array.isArray(j.data)) {
                console.log('zgzcw data count:', j.data.length);
                console.log('zgzcw sample:', JSON.stringify(j.data.slice(0, 3), null, 2));
            }
        } catch (e) {
            console.log('zgzcw not JSON, first 500 chars:', zgzcwData.slice(0, 500));
        }
    }
    
    // 3. 尝试 500.com 另一种 URL
    console.log('\n[3] 500.com alternative...');
    const wccData = await new Promise((resolve) => {
        const req = https.request({
            hostname: 'odds.500.com',
            path: '/jcfs/gzdata/' + dateNum + '.htm',
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout: 15000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(d));
        });
        req.on('error', e => resolve('ERROR: ' + e.message));
        req.on('timeout', () => { req.destroy(); resolve('TIMEOUT'); });
        req.end();
    });
    
    console.log('500.com wcc length:', wccData.length);
    if (wccData.length > 50) {
        console.log('500.com wcc first 300 chars:', wccData.slice(0, 300));
    }
}

main().catch(err => console.error(err));
