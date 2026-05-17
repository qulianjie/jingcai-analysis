const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const tasksDir = path.join(__dirname, 'tasks');

// Dates that still have gaps
const DATES = ['2026-05-03','2026-05-10','2026-05-12'];

function queryNotion(dateStr) {
    const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: dateStr } }, page_size: 100 });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); resolve((r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith(dateStr); })); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

function addPage(props) {
    const data = JSON.stringify({ parent: { database_id: DB_ID }, properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode)); else resolve(JSON.parse(b)); }); });
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
    let totalAdded = 0, totalUpdated = 0;
    
    for (const dateStr of DATES) {
        const dateDir = path.join(tasksDir, dateStr, 'data');
        if (!fs.existsSync(dateDir)) continue;
        
        const dirs = fs.readdirSync(dateDir).filter(d => d.startsWith('match'));
        const matchMap = {};
        for (const d of dirs) {
            const mp = path.join(dateDir, d, 'meta.json');
            if (fs.existsSync(mp)) {
                const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
                if (m.matchnum) matchMap[m.matchnum] = path.join(dateDir, d);
            }
        }
        
        const existing = await queryNotion(dateStr);
        const existingMap = {};
        for (const p of existing) {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            if (n.includes('分组统计')) continue;
            const mnMatch = n.match(/^([周][一二三四五六日]\d+)/);
            if (mnMatch) existingMap[mnMatch[1]] = p;
        }
        
        console.log(dateStr + ': 本地=' + Object.keys(matchMap).length + ', Notion=' + Object.keys(existingMap).length);
        
        for (const [mn, matchDir] of Object.entries(matchMap)) {
            if (existingMap[mn]) {
                // Update existing with any missing fields
                const page = existingMap[mn];
                const pred = page.properties['竞彩预测']?.rich_text?.[0]?.plain_text;
                const rqS = page.properties['让球指数胜']?.number;
                const ma = page.properties['竞彩澳门亚盘']?.rich_text?.[0]?.plain_text;
                
                if (!pred || !rqS || !ma) {
                    const metaPath = path.join(matchDir, 'meta.json');
                    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
                    
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
                    
                    const s1Path = path.join(matchDir, 'group01_europe', 'step1_europe_base.txt');
                    let ow = 0, od = 0, ol = 0;
                    if (fs.existsSync(s1Path)) {
                        const c1 = fs.readFileSync(s1Path, 'utf8');
                        const m = c1.match(/竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/);
                        if (m) { ow = parseFloat(m[4]) || 0; od = parseFloat(m[5]) || 0; ol = parseFloat(m[6]) || 0; }
                    }
                    
                    const fcPath = path.join(matchDir, 'final_conclusion.txt');
                    let prediction = '', confidence = '';
                    if (fs.existsSync(fcPath)) {
                        const fc = fs.readFileSync(fcPath, 'utf8');
                        const pm = fc.match(/竞彩预测[：:]\s*(.+)$/m);
                        const cm = fc.match(/信心[：:]\s*(.+)$/m);
                        if (pm) prediction = pm[1].trim();
                        if (cm) confidence = cm[1].trim();
                    }
                    
                    const props = {
                        '竞彩欧赔胜': { number: ow },
                        '竞彩欧赔平': { number: od },
                        '竞彩欧赔负': { number: ol },
                        '让球指数胜': { number: rq_win },
                        '让球指数平': { number: rq_draw },
                        '让球指数负': { number: rq_loss },
                    };
                    if (prediction) props['竞彩预测'] = { rich_text: [{ text: { content: prediction } }] };
                    if (confidence) props['风险提示'] = { rich_text: [{ text: { content: confidence } }] };
                    if (meta.macau_line) {
                        props['竞彩澳门亚盘'] = { rich_text: [{ text: { content: meta.macau_line } }] };
                        props['澳门亚盘'] = { rich_text: [{ text: { content: meta.macau_line } }] };
                    }
                    
                    await updatePage(page.id, props);
                    totalUpdated++;
                }
                continue;
            }
            
            // Add new record
            const metaPath = path.join(matchDir, 'meta.json');
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            
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
            
            const s1Path = path.join(matchDir, 'group01_europe', 'step1_europe_base.txt');
            let ow = 0, od = 0, ol = 0;
            if (fs.existsSync(s1Path)) {
                const c1 = fs.readFileSync(s1Path, 'utf8');
                const m = c1.match(/竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/);
                if (m) { ow = parseFloat(m[4]) || 0; od = parseFloat(m[5]) || 0; ol = parseFloat(m[6]) || 0; }
            }
            
            const fcPath = path.join(matchDir, 'final_conclusion.txt');
            let prediction = '', confidence = '';
            if (fs.existsSync(fcPath)) {
                const fc = fs.readFileSync(fcPath, 'utf8');
                const pm = fc.match(/竞彩预测[：:]\s*(.+)$/m);
                const cm = fc.match(/信心[：:]\s*(.+)$/m);
                if (pm) prediction = pm[1].trim();
                if (cm) confidence = cm[1].trim();
            }
            
            const mn2 = meta.matchnum;
            const name = `${mn2} ${meta.league} ${meta.home}vs${meta.away}`;
            const props = {
                Name: { title: [{ text: { content: name } }] },
                '比赛日期': { date: { start: dateStr } },
                '比赛': { rich_text: [{ text: { content: meta.home + 'vs' + meta.away } }] },
                '竞彩欧赔胜': { number: ow },
                '竞彩欧赔平': { number: od },
                '竞彩欧赔负': { number: ol },
                '让球指数胜': { number: rq_win },
                '让球指数平': { number: rq_draw },
                '让球指数负': { number: rq_loss },
            };
            if (prediction) props['竞彩预测'] = { rich_text: [{ text: { content: prediction } }] };
            if (confidence) props['风险提示'] = { rich_text: [{ text: { content: confidence } }] };
            if (meta.macau_line) {
                props['竞彩澳门亚盘'] = { rich_text: [{ text: { content: meta.macau_line } }] };
                props['澳门亚盘'] = { rich_text: [{ text: { content: meta.macau_line } }] };
            }
            
            try {
                await addPage(props);
                totalAdded++;
                console.log('  ➕ ' + mn2 + ' ' + meta.home + 'vs' + meta.away);
            } catch (e) {
                console.log('  ❌ ' + mn2 + ' ' + e.message);
            }
        }
    }
    
    console.log('\n完成! 新增=' + totalAdded + ', 更新=' + totalUpdated);
}

main().catch(e => console.error(e));
