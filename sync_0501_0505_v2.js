const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

function trunc1(v) {
    return Math.floor(v * 10) / 10;
}

function addPage(props) {
    const data = JSON.stringify({ parent: { database_id: DB_ID }, properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b.slice(0, 100))); else resolve(JSON.parse(b)); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function main() {
    const DATES = ['2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05'];
    let total = 0, errors = 0;
    
    for (const dateStr of DATES) {
        const dateDir = path.join(tasksDir, dateStr, 'data');
        if (!fs.existsSync(dateDir)) { console.log(dateStr + ': 无data目录'); continue; }
        
        const dirs = fs.readdirSync(dateDir).filter(d => d.startsWith('match'));
        console.log(dateStr + ': ' + dirs.length + '场');
        
        for (const d of dirs) {
            const matchDir = path.join(dateDir, d);
            const metaPath = path.join(matchDir, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const mn = meta.matchnum || '';
            if (!mn) continue;
            
            // Read step4 for handicap
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
            
            const macauLine = meta.macau_line || '';
            
            const name = `${mn} ${meta.league} ${meta.home}vs${meta.away}`;
            const props = {
                Name: { title: [{ text: { content: name } }] },
                '比赛日期': { date: { start: dateStr } },
                '比赛': { rich_text: [{ text: { content: meta.home + 'vs' + meta.away } }] },
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
            
            try {
                await addPage(props);
                total++;
                console.log('  ➕ ' + mn + ' ' + meta.home + 'vs' + meta.away);
            } catch (e) {
                errors++;
                console.log('  ❌ ' + mn + ' ' + e.message);
            }
            
            // Rate limit: 200ms between requests
            await sleep(200);
        }
    }
    
    console.log('\n完成! 新增 ' + total + ', 失败 ' + errors);
}

main().catch(e => console.error(e));
