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

async function main() {
    // 先检查一场，看看Notion里这两列当前是什么数据
    const dateStr = '2026-05-09';
    const result = await queryNotionByDate(dateStr);
    const pages = (result.results || []).filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
    
    console.log(dateStr + ': Notion=' + pages.length);
    for (const p of pages.slice(0, 5)) {
        const mn = p.properties.Name?.title?.[0]?.plain_text || '';
        const oTrend = p.properties['欧赔趋势']?.rich_text?.[0]?.plain_text || '';
        const mYapan = p.properties['澳门亚盘']?.rich_text?.[0]?.plain_text || '';
        console.log(mn + ' | 欧赔趋势=' + oTrend + ' | 澳门亚盘=' + mYapan);
    }
    
    // 再看看md文件里的数据
    const mdPath = path.join(tasksDir, dateStr, '周六001_奥克兰FCvs阿德莱德.md');
    if (fs.existsSync(mdPath)) {
        console.log('\n=== MD文件数据 ===');
        const content = fs.readFileSync(mdPath, 'utf8');
        const lines = content.split('\n');
        for (const line of lines) {
            if (line.includes('| 欧赔趋势 |') || line.includes('| 澳门亚盘 |')) {
                console.log(line);
            }
        }
    }
}

main().catch(e => console.error(e));
