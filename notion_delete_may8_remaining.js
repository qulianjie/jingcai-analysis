// 检查Notion中5月8日还剩多少周六/周日
const https = require('https');

const NOTION_API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function notionRequest(method, urlPath, body) {
    return new Promise((resolve, reject) => {
        const data = body ? JSON.stringify(body) : null;
        const req = https.request({
            hostname: 'api.notion.com',
            path: urlPath,
            method: method,
            headers: {
                'Authorization': 'Bearer ' + NOTION_API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                ...(data && {'Content-Length': Buffer.byteLength(data)})
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => {
                try { resolve(JSON.parse(b)); } catch(e) { resolve(b); }
            });
        });
        req.on('error', reject);
        if (data) req.write(data);
        req.end();
    });
}

async function main() {
    const payload = {
        filter: {property: "比赛日期", date: {on_or_after: "2026-05-08"}},
        page_size: 100
    };
    
    const result = await notionRequest('POST', `/v1/databases/${DB_ID}/query`, payload);
    console.log('Total entries: ' + (result.results?.length || 0));
    
    const toDelete = [];
    const dateCounts = {};
    
    result.results?.forEach(row => {
        const match = row.properties['比赛']?.rich_text?.[0]?.plain_text || '';
        const dt = row.properties['比赛日期']?.date?.start || '';
        
        if (dt.startsWith('2026-05-08') && (match.includes('周六') || match.includes('周日'))) {
            toDelete.push({id: row.id, match, date: dt});
        }
        
        dateCounts[dt] = (dateCounts[dt] || 0) + 1;
    });
    
    console.log('\nDate distribution:');
    for (const [dt, cnt] of Object.entries(dateCounts).sort()) {
        console.log('  ' + dt + ': ' + cnt);
    }
    
    console.log('\nRemaining to delete: ' + toDelete.length);
    toDelete.forEach(e => console.log('  ' + e.match + ' | ' + e.date));
    
    if (toDelete.length === 0) {
        console.log('All 2026-05-08 周六/周日 entries deleted!');
        return;
    }
    
    // Delete remaining
    for (const e of toDelete) {
        await notionRequest('PATCH', `/v1/pages/${e.id}`, {archived: true});
        console.log('Deleted: ' + e.match);
    }
    console.log('\nDone. Deleted remaining ' + toDelete.length + ' entries.');
}

main().catch(e => console.error(e));
