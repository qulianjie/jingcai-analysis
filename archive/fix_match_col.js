const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

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

function updatePage(pageId, props) {
    const data = JSON.stringify({ properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages/' + pageId, method: 'PATCH', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode)); else resolve(JSON.parse(b)); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    const DATES = ['2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05'];
    let totalUpdated = 0;
    
    for (const dateStr of DATES) {
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            return !n.includes('分组统计');
        });
        
        let dateUpdated = 0;
        for (const page of pages) {
            const nameField = page.properties.Name?.title?.[0]?.plain_text || '';
            const mnMatch = nameField.match(/^([周][一二三四五六日]\d+)/);
            if (!mnMatch) continue;
            
            const matchNum = mnMatch[1];
            const currentMatch = page.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            
            // Update "比赛" column to be just "周XNNN"
            if (currentMatch !== matchNum) {
                await updatePage(page.id, { '比赛': { rich_text: [{ text: { content: matchNum } }] } });
                dateUpdated++;
            }
        }
        
        console.log(dateStr + ': 更新 ' + dateUpdated + '/' + pages.length);
        totalUpdated += dateUpdated;
    }
    
    console.log('\n完成! 共更新 ' + totalUpdated + ' 场');
}

main().catch(e => console.error(e));
