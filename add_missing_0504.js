const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function addPage(props) {
    const data = JSON.stringify({ parent: { database_id: DB_ID }, properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/pages', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b.slice(0, 200))); else resolve(JSON.parse(b)); }); });
        req.on('error', reject); req.write(data); req.end();
    });
}

async function main() {
    const targets = [
        { date: '2026-05-04', matchnum: '周一001', dir: 'match1_切尔西__诺丁汉' },
        { date: '2026-05-04', matchnum: '周一005', dir: 'match5_哈尔姆斯__布鲁马波' },
    ];
    
    for (const t of targets) {
        const base = `jingcai/tasks/${t.date}/data/${t.dir}`;
        const meta = JSON.parse(fs.readFileSync(path.join(base, 'meta.json'), 'utf8'));
        
        // Read step4
        const s4Path = path.join(base, 'group02_handicap', 'step4_handicap_base.txt');
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
        
        // Read step1
        const s1Path = path.join(base, 'group01_europe', 'step1_europe_base.txt');
        let ow = 0, od = 0, ol = 0;
        if (fs.existsSync(s1Path)) {
            const c1 = fs.readFileSync(s1Path, 'utf8');
            const m = c1.match(/竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/);
            if (m) { ow = parseFloat(m[4]) || 0; od = parseFloat(m[5]) || 0; ol = parseFloat(m[6]) || 0; }
        }
        
        // Prediction
        const fcPath = path.join(base, 'final_conclusion.txt');
        let prediction = '', confidence = '';
        if (fs.existsSync(fcPath)) {
            const fc = fs.readFileSync(fcPath, 'utf8');
            const pm = fc.match(/竞彩预测[：:]\s*(.+)$/m);
            const cm = fc.match(/信心[：:]\s*(.+)$/m);
            if (pm) prediction = pm[1].trim();
            if (cm) confidence = cm[1].trim();
        }
        
        const name = `${t.matchnum} ${meta.league} ${meta.home}vs${meta.away}`;
        const props = {
            Name: { title: [{ text: { content: name } }] },
            '比赛日期': { date: { start: t.date } },
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
            console.log(`✅ ${t.matchnum} ${meta.home}vs${meta.away}`);
        } catch (e) {
            console.log(`❌ ${t.matchnum} ${e.message}`);
        }
    }
}

main();
