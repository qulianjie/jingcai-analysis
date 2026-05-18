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

function extractMatchNum(name) {
    const m = name.match(/^([周][一二三四五六日]\d+)/);
    return m ? m[1] : '';
}

async function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function main() {
    const DATES = ['2026-05-10','2026-05-11'];
    let totalUpdated = 0;
    
    for (const dateStr of DATES) {
        const dateDir = path.join(tasksDir, dateStr);
        if (!fs.existsSync(dateDir)) continue;
        
        const mdFiles = fs.readdirSync(dateDir).filter(f => f.endsWith('.md') && !f.includes('分组统计'));
        const mdMap = {};
        for (const f of mdFiles) {
            const mnMatch = f.match(/^([周][一二三四五六日]\d+)/);
            if (mnMatch) mdMap[mnMatch[1]] = path.join(dateDir, f);
        }
        
        const result = await queryNotionByDate(dateStr);
        const pages = (result.results || []).filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        
        console.log(dateStr + ': Notion=' + pages.length + ', md文件=' + mdFiles.length);
        
        for (const page of pages) {
            const nameField = page.properties.Name?.title?.[0]?.plain_text || '';
            const mn = extractMatchNum(nameField);
            if (!mn || !mdMap[mn]) continue;
            
            const mdPath = mdMap[mn];
            const content = fs.readFileSync(mdPath, 'utf8');
            
            let oTrend = '', mYapan = '';
            const lines = content.split('\n');
            for (const line of lines) {
                if (line.includes('| 欧赔趋势 |')) {
                    const match = line.match(/\|\s*欧赔趋势\s*\|\s*(.+?)\s*\|\s*(\d+)%\s*\|/);
                    if (match) oTrend = match[1].trim() + ' | ' + match[2] + '%';
                }
                if (line.includes('| 澳门亚盘 |')) {
                    const match = line.match(/\|\s*澳门亚盘\s*\|\s*(.+?)\s*\|\s*(\d+)%\s*\|/);
                    if (match) mYapan = match[1].trim() + ' | ' + match[2] + '%';
                }
            }
            
            if (oTrend || mYapan) {
                const props = {};
                if (oTrend) props['欧赔趋势'] = { rich_text: [{ text: { content: oTrend } }] };
                if (mYapan) props['澳门亚盘'] = { rich_text: [{ text: { content: mYapan } }] };
                await updatePage(page.id, props);
                totalUpdated++;
                console.log('  ' + mn + ' | 欧赔趋势=' + oTrend + ' | 澳门亚盘=' + mYapan);
            }
            
            await sleep(300);
        }
    }
    
    console.log('\n完成! 更新 ' + totalUpdated + ' 场');
}

main().catch(e => console.error(e));
