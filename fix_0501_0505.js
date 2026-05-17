const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const DATES = ['2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05',
               '2026-05-06','2026-05-08','2026-05-09','2026-05-10','2026-05-11'];
const tasksDir = path.join(__dirname, 'tasks');

function queryNotion(dateStr) {
    const data = JSON.stringify({ filter: { property: '比赛日期', date: { on_or_after: dateStr } }, page_size: 100 });
    return new Promise((resolve, reject) => {
        const req = https.request({ hostname: 'api.notion.com', path: '/v1/databases/' + DB_ID + '/query', method: 'POST', headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, res => { let b = ''; res.on('data', c => b += c); res.on('end', () => { const r = JSON.parse(b); resolve((r.results || []).filter(p => { const dt = p.properties['比赛日期']?.date?.start; return dt && dt.startsWith(dateStr); })) }); });
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
    let totalUpdated = 0;
    let totalSkipped = 0;
    
    for (const dateStr of DATES) {
        const dateDir = path.join(tasksDir, dateStr, 'data');
        if (!fs.existsSync(dateDir)) { console.log(dateStr + ': 无data目录'); continue; }
        
        const dirs = fs.readdirSync(dateDir).filter(d => d.startsWith('match'));
        const matchMap = {};
        for (const d of dirs) {
            const mp = path.join(dateDir, d, 'meta.json');
            if (fs.existsSync(mp)) {
                const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
                if (m.matchnum) matchMap[m.matchnum] = { meta: m, dir: path.join(dateDir, d) };
            }
        }
        
        const existing = await queryNotion(dateStr);
        console.log(dateStr + ': Notion有' + existing.length + '场, 本地有' + Object.keys(matchMap).length + '场');
        
        for (const page of existing) {
            const nameField = page.properties.Name?.title?.[0]?.plain_text || '';
            if (nameField.includes('分组统计')) continue;
            
            // Extract matchnum from Notion name
            const mnMatch = nameField.match(/^([周][一二三四五六日]\d+)/);
            if (!mnMatch) continue;
            const mn = mnMatch[1];
            const info = matchMap[mn];
            if (!info) { console.log('  ⚠️ ' + mn + ' 本地无数据'); continue; }
            
            const meta = info.meta;
            const matchDir = info.dir;
            
            // Check if this record needs fixing (undefined values)
            const homeVal = page.properties['比赛']?.rich_text?.[0]?.plain_text || '';
            if (homeVal === 'undefinedvsundefined' || !homeVal) {
                // Fix basic fields
                const fixProps = {
                    Name: { title: [{ text: { content: `${mn} ${meta.league} ${meta.home}vs${meta.away}` } }] },
                    '比赛': { rich_text: [{ text: { content: meta.home + 'vs' + meta.away } }] },
                };
                
                // Read step1 for odds
                const s1Path = path.join(matchDir, 'group01_europe', 'step1_europe_base.txt');
                if (fs.existsSync(s1Path)) {
                    const c1 = fs.readFileSync(s1Path, 'utf8');
                    const m = c1.match(/竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/);
                    if (m) {
                        fixProps['竞彩欧赔胜'] = { number: parseFloat(m[4]) || 0 };
                        fixProps['竞彩欧赔平'] = { number: parseFloat(m[5]) || 0 };
                        fixProps['竞彩欧赔负'] = { number: parseFloat(m[6]) || 0 };
                        fixProps['欧赔趋势'] = { rich_text: [{ text: { content: `初盘${m[1]}/${m[2]}/${m[3]}→即时${m[4]}/${m[5]}/${m[6]}` } }] };
                    }
                }
                
                // Read step4 for handicap (FIXED: parts[5/6/7])
                const s4Path = path.join(matchDir, 'group02_handicap', 'step4_handicap_base.txt');
                if (fs.existsSync(s4Path)) {
                    const c4 = fs.readFileSync(s4Path, 'utf8');
                    for (const line of c4.split('\n')) {
                        if (!line.includes('|')) continue;
                        const parts = line.split('|').map(p => p.trim()).filter(p => p);
                        if (parts.length >= 8 && parts[0] === '竞彩官方') {
                            fixProps['让球指数胜'] = { number: parseFloat(parts[5]) || 0 };
                            fixProps['让球指数平'] = { number: parseFloat(parts[6]) || 0 };
                            fixProps['让球指数负'] = { number: parseFloat(parts[7]) || 0 };
                            break;
                        }
                    }
                }
                
                // Macau line
                if (meta.macau_line) {
                    fixProps['竞彩澳门亚盘'] = { rich_text: [{ text: { content: meta.macau_line } }] };
                    fixProps['澳门亚盘'] = { rich_text: [{ text: { content: meta.macau_line } }] };
                }
                
                // Prediction
                const fcPath = path.join(matchDir, 'final_conclusion.txt');
                if (fs.existsSync(fcPath)) {
                    const fc = fs.readFileSync(fcPath, 'utf8');
                    const pm = fc.match(/竞彩预测[：:]\s*(.+)$/m);
                    const cm = fc.match(/信心[：:]\s*(.+)$/m);
                    if (pm) fixProps['竞彩预测'] = { rich_text: [{ text: { content: pm[1].trim() } }] };
                    if (cm) fixProps['风险提示'] = { rich_text: [{ text: { content: cm[1].trim() } }] };
                }
                
                await updatePage(page.id, fixProps);
                totalUpdated++;
                console.log('  ✅ ' + mn + ' ' + meta.home + 'vs' + meta.away);
            } else {
                totalSkipped++;
            }
        }
    }
    
    console.log('\n完成! 修正' + totalUpdated + '场, 跳过' + totalSkipped + '场');
}

main().catch(e => console.error(e));
