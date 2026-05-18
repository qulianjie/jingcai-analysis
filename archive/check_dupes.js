const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function queryNotionByDate(dateStr) {
    const data = JSON.stringify({
        filter: { and: [
            { property: '比赛日期', date: { on_or_after: dateStr } },
            { property: '比赛日期', date: { on_or_before: dateStr } }
        ]},
        page_size: 100
    });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { try { resolve(JSON.parse(b)); } catch(e) { reject(e); } }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    let hasDuplicates = false;
    
    for (let d = 1; d <= 12; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        
        // Check for duplicates in "比赛" column
        const matchNums = {};
        const badMatch = [];
        for (const p of pages) {
            const match = p.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            const name = p.properties.Name?.title?.[0]?.plain_text || '';
            if (!match.startsWith('周')) {
                badMatch.push(name);
            }
            if (matchNums[match]) {
                console.log('⚠️ ' + dateStr + ' 重复: ' + match);
                console.log('  1: ' + matchNums[match].name + ' (' + matchNums[match].id + ')');
                console.log('  2: ' + name + ' (' + p.id + ')');
                hasDuplicates = true;
            } else {
                matchNums[match] = { name, id: p.id };
            }
        }
        
        if (badMatch.length > 0) {
            console.log(dateStr + ': ' + badMatch.length + ' 场"比赛"列不以"周"开头');
        }
    }
    
    if (!hasDuplicates) {
        console.log('✅ 无重复记录');
    }
}

main().catch(e => console.error(e));
