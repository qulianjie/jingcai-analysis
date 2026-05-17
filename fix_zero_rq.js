const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

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
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages/' + pageId, method: 'PATCH', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b)); else resolve(JSON.parse(b)); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    // Dates that showed zero RQ issues
    const targets = {
        '2026-05-02': ['周六003'],
        '2026-05-03': ['周日029'], // 美职足 - 可能确实没数据
        '2026-05-08': ['周日020','周日019','周日018','周日006','周六028','周六011'],
        '2026-05-09': ['周六019','周六027','周六005','周六011'], // from earlier audit
        '2026-05-10': ['周日014'],
        '2026-05-11': ['周一002','周一003','周一006'],
        '2026-05-12': []
    };
    
    for (const [dateStr, matchNums] of Object.entries(targets)) {
        const dateDir = path.join(tasksDir, dateStr, 'data');
        if (!fs.existsSync(dateDir)) { console.log(dateStr + ': 无data目录'); continue; }
        
        const results = await queryNotion(dateStr);
        
        for (const mn of matchNums) {
            const page = results.find(p => {
                const n = p.properties.Name?.title?.[0]?.plain_text || '';
                return n.startsWith(mn);
            });
            if (!page) { console.log(dateStr + ' ' + mn + ': Notion中未找到'); continue; }
            
            // Find local match dir
            let matchDir = null;
            for (const d of fs.readdirSync(dateDir).filter(x => x.startsWith('match'))) {
                const mp = path.join(dateDir, d, 'meta.json');
                if (fs.existsSync(mp)) {
                    const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
                    if (m.matchnum === mn) { matchDir = path.join(dateDir, d); break; }
                }
            }
            if (!matchDir) { console.log(dateStr + ' ' + mn + ': 本地未找到'); continue; }
            
            // Read step4
            const s4Path = path.join(matchDir, 'group02_handicap', 'step4_handicap_base.txt');
            let rq_win = 0, rq_draw = 0, rq_loss = 0;
            if (fs.existsSync(s4Path)) {
                const c4 = fs.readFileSync(s4Path, 'utf8');
                for (const line of c4.split('\n')) {
                    if (!line.includes('|')) continue;
                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                    if (parts.length >= 8 && parts[0] === '竞彩官方') {
                        rq_win = parseFloat(parts[5]) || 0;
                        rq_draw = parseFloat(parts[6]) || 0;
                        rq_loss = parseFloat(parts[7]) || 0;
                        break;
                    }
                }
            }
            
            const props = {
                '让球指数胜': { number: rq_win },
                '让球指数平': { number: rq_draw },
                '让球指数负': { number: rq_loss },
            };
            await updatePage(page.id, props);
            console.log(dateStr + ' ' + mn + ' | RQ:' + rq_win + '/' + rq_draw + '/' + rq_loss);
        }
    }
    
    console.log('\n完成!');
}

main().catch(e => console.error(e));
