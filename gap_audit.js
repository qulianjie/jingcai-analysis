const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

async function queryDate(dateStr) {
    const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: dateStr } }, page_size: 100 });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); resolve((r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith(dateStr); })); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    let notionTotal = 0, localTotal = 0;
    
    for (let d = 1; d <= 12; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const results = await queryDate(dateStr);
        const notionGames = results.filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        
        const dateDir = path.join(tasksDir, dateStr, 'data');
        let localGames = 0;
        if (fs.existsSync(dateDir)) {
            localGames = fs.readdirSync(dateDir).filter(d => d.startsWith('match')).length;
        }
        
        notionTotal += notionGames.length;
        localTotal += localGames;
        
        // Find missing
        const existingMns = new Set();
        for (const p of notionGames) {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            const m = n.match(/^([周][一二三四五六日]\d+)/);
            if (m) existingMns.add(m[1]);
        }
        
        if (fs.existsSync(dateDir)) {
            const dirs = fs.readdirSync(dateDir).filter(d => d.startsWith('match'));
            for (const dir of dirs) {
                const mp = path.join(dateDir, dir, 'meta.json');
                if (fs.existsSync(mp)) {
                    const meta = JSON.parse(fs.readFileSync(mp, 'utf8'));
                    if (meta.matchnum && !existingMns.has(meta.matchnum)) {
                        // Check if in notion but with different date
                        const wrongDate = results.find(p => {
                            const n = p.properties.Name?.title?.[0]?.plain_text || '';
                            return n.startsWith(meta.matchnum);
                        });
                        if (wrongDate) {
                            console.log('⚠️ ' + meta.matchnum + ' 在Notion中但日期是: ' + wrongDate.properties['比赛日期']?.date?.start);
                        } else {
                            console.log('❌ ' + meta.matchnum + ' 不在Notion中');
                        }
                    }
                }
            }
        }
    }
    
    console.log('\nNotion总计: ' + notionTotal + ' 场');
    console.log('本地总计: ' + localTotal + ' 场');
    console.log('差距: ' + (localTotal - notionTotal) + ' 场');
}

main().catch(e => console.error(e));
