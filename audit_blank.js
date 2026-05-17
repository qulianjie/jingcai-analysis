const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// Check Notion for dates 5-1 to 5-11
async function queryNotion(dateStr) {
    const data = JSON.stringify({
        filter: { property: '比赛日期', date: { on_or_after: dateStr } },
        page_size: 100
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/databases/' + DB_ID + '/query',
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => {
                const r = JSON.parse(b);
                // Filter to only this date
                const results = (r.results || []).filter(p => {
                    const dt = p.properties['比赛日期']?.date?.start;
                    return dt && dt.startsWith(dateStr);
                });
                resolve(results);
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    const dates = [];
    for (let d = 1; d <= 11; d++) {
        dates.push('2026-05-' + String(d).padStart(2, '0'));
    }
    
    let totalCount = 0;
    for (const date of dates) {
        const results = await queryNotion(date);
        const games = results.filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        let blankRq = 0, blankMa = 0;
        for (const p of games) {
            const rq = p.properties['让球指数胜']?.number;
            const ma = p.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text;
            if (rq === null || rq === undefined) blankRq++;
            if (!ma) blankMa++;
        }
        console.log(date + ': ' + games.length + '场, 让球空白:' + blankRq + ', 澳门亚盘空白:' + blankMa);
        totalCount += games.length;
    }
    console.log('\n总计:' + totalCount + '场');
}

main().catch(e => console.error(e));
