const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

// Helper: truncate to 1 decimal
function trunc1(v) {
    return Math.floor(v * 10) / 10;
}

function queryNotion(dateStr) {
    const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: dateStr } }, page_size: 100 });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); resolve((r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith(dateStr); })); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

function updatePage(pageId, props) {
    const data = JSON.stringify({ properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages/' + pageId, method: 'PATCH', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b.slice(0, 200))); else resolve(JSON.parse(b)); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    let totalUpdated = 0;
    
    for (let d = 1; d <= 11; d++) {
        const dateStr = '2026-05-' + String(d).padStart(2, '0');
        const dateDir = path.join(tasksDir, dateStr, 'data');
        if (!fs.existsSync(dateDir)) { console.log(dateStr + ': 无data目录'); continue; }
        
        // Build local match map
        const dirs = fs.readdirSync(dateDir).filter(x => x.startsWith('match'));
        const matchMap = {};
        for (const dir of dirs) {
            const mp = path.join(dateDir, dir, 'meta.json');
            if (fs.existsSync(mp)) {
                const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
                if (m.matchnum) matchMap[m.matchnum] = path.join(dateDir, dir);
            }
        }
        
        // Query Notion
        const results = await queryNotion(dateStr);
        const games = results.filter(p => { const n = p.properties.Name?.title?.[0]?.plain_text || ''; return !n.includes('分组统计'); });
        
        console.log(dateStr + ': Notion=' + games.length + ', 本地=' + Object.keys(matchMap).length);
        
        for (const page of games) {
            const nameField = page.properties.Name?.title?.[0]?.plain_text || '';
            const mnMatch = nameField.match(/^([周][一二三四五六日]\d+)/);
            if (!mnMatch) continue;
            const mn = mnMatch[1];
            const matchDir = matchMap[mn];
            if (!matchDir) continue;
            
            const metaPath = path.join(matchDir, 'meta.json');
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            
            // Read step4 for handicap odds
            // Format: | 竞彩官方 | 让球 | 初胜 | 初平 | 初负 | 即时胜 | 即时平 | 即时负 |
            // parts:  [0]         [1]   [2]   [3]   [4]   [5]     [6]     [7]
            const s4Path = path.join(matchDir, 'group02_handicap', 'step4_handicap_base.txt');
            let rq_init_win = 0, rq_init_draw = 0, rq_init_loss = 0;
            let rq_live_win = 0, rq_live_draw = 0, rq_live_loss = 0;
            if (fs.existsSync(s4Path)) {
                const c4 = fs.readFileSync(s4Path, 'utf8');
                for (const line of c4.split('\n')) {
                    if (!line.includes('|')) continue;
                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                    if (parts.length >= 8 && parts[0] === '竞彩官方') {
                        rq_init_win = parseFloat(parts[2]) || 0;
                        rq_init_draw = parseFloat(parts[3]) || 0;
                        rq_init_loss = parseFloat(parts[4]) || 0;
                        rq_live_win = parseFloat(parts[5]) || 0;
                        rq_live_draw = parseFloat(parts[6]) || 0;
                        rq_live_loss = parseFloat(parts[7]) || 0;
                        break;
                    }
                }
            }
            
            // Macau line from meta.json
            const macauLine = meta.macau_line || '';
            
            // Build update props (truncate to 1 decimal)
            const props = {
                '让球指数胜': { number: trunc1(rq_live_win) },
                '让球指数平': { number: trunc1(rq_live_draw) },
                '让球指数负': { number: trunc1(rq_live_loss) },
                '终盘让球指数胜': { number: trunc1(rq_init_win) },
                '终盘让球指数平': { number: trunc1(rq_init_draw) },
                '终盘让球指数负': { number: trunc1(rq_init_loss) },
            };
            if (macauLine) {
                props['竞彩澳门亚盘'] = { rich_text: [{ text: { content: macauLine } }] };
                props['终盘竞彩澳门亚盘'] = { rich_text: [{ text: { content: macauLine } }] };
            }
            
            await updatePage(page.id, props);
            totalUpdated++;
        }
    }
    
    console.log('\n完成! 更新 ' + totalUpdated + ' 场');
}

main().catch(e => console.error(e));
