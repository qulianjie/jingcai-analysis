const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// Dates to process
const DATES = [
    '2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05',
    '2026-05-06', '2026-05-08', '2026-05-09', '2026-05-10', '2026-05-11'
];

function queryNotion(dateStr) {
    const data = JSON.stringify({
        filter: { property: '比赛日期', date: { on_or_after: dateStr } },
        page_size: 100
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/databases/' + DB_ID + '/query',
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => {
                const r = JSON.parse(b);
                const results = (r.results || []).filter(p => {
                    const dt = p.properties['比赛日期']?.date?.start;
                    return dt && dt.startsWith(dateStr);
                });
                resolve(results);
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

function updatePage(pageId, props) {
    const data = JSON.stringify({ properties: props });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages/' + pageId,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => {
                if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b));
                else resolve(JSON.parse(b));
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

function addPage(props) {
    const data = JSON.stringify({ 
        parent: { database_id: DB_ID }, 
        properties: props 
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages',
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => {
                if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + b));
                else resolve(JSON.parse(b));
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

// Read match data from local files
function readMatchData(matchDir) {
    const result = {};
    
    // meta.json
    const metaPath = path.join(matchDir, 'meta.json');
    if (fs.existsSync(metaPath)) {
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        result.matchnum = meta.matchnum || '';
        result.league = meta.league || '';
        result.homeTeam = meta.homeTeam || '';
        result.awayTeam = meta.awayTeam || '';
        result.macau_line = meta.macau_line || '';
        result.fid = meta.fid || '';
        result.matchDate = meta.matchDate || '';
        result.matchTime = meta.matchTime || '';
    }
    
    // step1: 欧赔基础
    const s1Path = path.join(matchDir, 'group01_europe', 'step1_europe_base.txt');
    if (fs.existsSync(s1Path)) {
        const c1 = fs.readFileSync(s1Path, 'utf8');
        const m = c1.match(/竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([^|]+)/);
        if (m) {
            result.oupei_base = `初盘${m[1]}/${m[2]}/${m[3]}→即时${m[4]}/${m[5]}/${m[6]} 变化${m[7].trim()}`;
            result.oupei_win = parseFloat(m[4]) || 0;
            result.oupei_draw = parseFloat(m[5]) || 0;
            result.oupei_loss = parseFloat(m[6]) || 0;
        }
    }
    
    // step2: 竞彩同赔
    const s2Path = path.join(matchDir, 'group01_europe', 'step2_jingcai_same.txt');
    if (fs.existsSync(s2Path)) {
        const c2 = fs.readFileSync(s2Path, 'utf8');
        const countM = c2.match(/竞彩同赔\s*共\s*(\d+)\s*场/);
        const winM = c2.match(/胜(\d+)\s*平(\d+)\s*负(\d+)/);
        if (countM) {
            result.jingcai_same = `共${countM[1]}场`;
            if (winM) result.jingcai_same += ` 胜${winM[1]}平${winM[2]}负${winM[3]}`;
        }
    }
    
    // step3: IW同赔
    const s3Path = path.join(matchDir, 'group01_europe', 'step3_iw_same.txt');
    if (fs.existsSync(s3Path)) {
        const c3 = fs.readFileSync(s3Path, 'utf8');
        const countM = c3.match(/IW同赔\s*共\s*(\d+)\s*场/);
        const winM = c3.match(/胜(\d+)\s*平(\d+)\s*负(\d+)/);
        if (countM) {
            result.iw_same = `共${countM[1]}场`;
            if (winM) result.iw_same += ` 胜${winM[1]}平${winM[2]}负${winM[3]}`;
        }
    }
    
    // step4: 让球基础 (FIXED: parts[5/6/7] not [6/7/8])
    const s4Path = path.join(matchDir, 'group02_handicap', 'step4_handicap_base.txt');
    if (fs.existsSync(s4Path)) {
        const c4 = fs.readFileSync(s4Path, 'utf8');
        for (const line of c4.split('\n')) {
            if (!line.includes('|')) continue;
            const parts = line.split('|').map(p => p.trim()).filter(p => p);
            if (parts.length >= 8 && parts[0] === '竞彩官方') {
                result.rq_init_win = parseFloat(parts[5]) || 0;
                result.rq_init_draw = parseFloat(parts[6]) || 0;
                result.rq_init_loss = parseFloat(parts[7]) || 0;
                break;
            }
        }
    }
    
    // step5: 让球同赔
    const s5Path = path.join(matchDir, 'group02_handicap', 'step5_handicap_same.txt');
    if (fs.existsSync(s5Path)) {
        const c5 = fs.readFileSync(s5Path, 'utf8');
        const countM = c5.match(/让球同赔\s*共\s*(\d+)\s*场/);
        const winM = c5.match(/胜(\d+)\s*平(\d+)\s*负(\d+)/);
        if (countM) {
            result.rq_same = `共${countM[1]}场`;
            if (winM) result.rq_same += ` 胜${winM[1]}平${winM[2]}负${winM[3]}`;
        }
    }
    
    // step6: 亚盘基础
    const s6Path = path.join(matchDir, 'group03_asian', 'step6_asian_base.txt');
    if (fs.existsSync(s6Path)) {
        const c6 = fs.readFileSync(s6Path, 'utf8');
        for (const line of c6.split('\n')) {
            if (!line.includes('澳门')) continue;
            const parts = line.split('|').map(p => p.trim()).filter(p => p);
            if (parts.length >= 3) {
                result.macau_init = parts[2] || '';
                result.macau_live = parts[parts.length - 1] || '';
                break;
            }
        }
    }
    
    // step7: 澳门亚盘同赔
    const s7Path = path.join(matchDir, 'group03_asian', 'step7_macau_same.txt');
    if (fs.existsSync(s7Path)) {
        const c7 = fs.readFileSync(s7Path, 'utf8');
        const countM = c7.match(/澳门同赔\s*共\s*(\d+)\s*场/);
        if (countM) {
            result.macau_same = `共${countM[1]}场`;
        }
    }
    
    // step8: 历史亚盘统计
    const s8Path = path.join(matchDir, 'group03_asian', 'step8_1923_asian_stats.txt');
    if (fs.existsSync(s8Path)) {
        const c8 = fs.readFileSync(s8Path, 'utf8');
        const m = c8.match(/共(\d+)场/);
        if (m) result.asian_stats = `共${m[1]}场`;
    }
    
    // final_conclusion.txt - 最终预测
    const fcPath = path.join(matchDir, 'final_conclusion.txt');
    if (fs.existsSync(fcPath)) {
        const fc = fs.readFileSync(fcPath, 'utf8');
        const predM = fc.match(/竞彩预测[：:]\s*(.+)$/m);
        const confM = fc.match(/信心[：:]\s*(.+)$/m);
        if (predM) result.prediction = predM[1].trim();
        if (confM) result.confidence = confM[1].trim();
    }
    
    // final_report.md
    const frPath = path.join(matchDir, 'final_report.md');
    if (fs.existsSync(frPath)) {
        result.report = fs.readFileSync(frPath, 'utf8').slice(0, 2000);
    }
    
    // step25: 庄家盈亏
    const s25Path = path.join(matchDir, 'step25_zjky.json');
    if (fs.existsSync(s25Path)) {
        const s25 = JSON.parse(fs.readFileSync(s25Path, 'utf8'));
        result.zjky = s25.zjky || '';
        result.zjkyDirection = s25.direction || '';
        result.zjkyRatio = s25.ratio || '';
    }
    
    // panlu_match
    const pmPath = path.join(matchDir, 'step24_panlu_match.json');
    if (fs.existsSync(pmPath)) {
        const pm = JSON.parse(fs.readFileSync(pmPath, 'utf8'));
        result.panlu = pm.summary || '';
    }
    
    // baijia comparison
    const s19Path = path.join(matchDir, 'group06_baijia', 'step19_baijia_compare.txt');
    if (fs.existsSync(s19Path)) {
        const c19 = fs.readFileSync(s19Path, 'utf8');
        const m = c19.match(/百家对比[：:]\s*(.+)$/m);
        if (m) result.baijia = m[1].trim();
    }
    
    return result;
}

function buildNotionProps(matchNum, data, dateStr) {
    const name = `${matchNum} ${data.league} ${data.homeTeam}vs${data.awayTeam}`;
    const props = {
        Name: { title: [{ text: { content: name } }] },
        '比赛日期': { date: { start: dateStr } }
    };
    
    // 比赛 (Name)
    props['比赛'] = { rich_text: [{ text: { content: `${data.homeTeam}vs${data.awayTeam}` } }] };
    
    // 竞彩预测
    if (data.prediction) {
        props['竞彩预测'] = { rich_text: [{ text: { content: data.prediction } }] };
    }
    
    // 竞彩信心
    if (data.confidence) {
        props['风险提示'] = { rich_text: [{ text: { content: data.confidence } }] };
    }
    
    // 欧赔指数
    if (data.oupei_win) props['竞彩欧赔胜'] = { number: data.oupei_win };
    if (data.oupei_draw) props['竞彩欧赔平'] = { number: data.oupei_draw };
    if (data.oupei_loss) props['竞彩欧赔负'] = { number: data.oupei_loss };
    
    // 欧赔趋势
    if (data.oupei_base) {
        props['欧赔趋势'] = { rich_text: [{ text: { content: data.oupei_base } }] };
    }
    
    // 让球指数 (FIXED: parts[5/6/7])
    if (data.rq_init_win) props['让球指数胜'] = { number: data.rq_init_win };
    if (data.rq_init_draw) props['让球指数平'] = { number: data.rq_init_draw };
    if (data.rq_init_loss) props['让球指数负'] = { number: data.rq_init_loss };
    
    // 澳门亚盘
    const macauText = data.macau_line || data.macau_live || data.macau_init || '';
    if (macauText) {
        props['竞彩澳门亚盘'] = { rich_text: [{ text: { content: macauText } }] };
        props['澳门亚盘'] = { rich_text: [{ text: { content: macauText } }] };
    }
    
    // IW同赔
    if (data.iw_same) {
        props['IW同赔'] = { rich_text: [{ text: { content: data.iw_same } }] };
    }
    
    // 百家对比
    if (data.baijia) {
        props['百家对比'] = { rich_text: [{ text: { content: data.baijia } }] };
    }
    
    // 盘路匹配
    if (data.panlu) {
        props['风险提示'] = { rich_text: [{ text: { content: (props['风险提示']?.rich_text?.[0]?.plain_text || '') + ' | 盘路:' + data.panlu } }] };
    }
    
    // 庄家盈亏
    if (data.zjky) {
        props['步25_庄家盈亏'] = { rich_text: [{ text: { content: data.zjky } }] };
    }
    if (data.zjkyDirection) {
        props['步26_庄家最看好'] = { rich_text: [{ text: { content: data.zjkyDirection } }] };
    }
    
    // 最终报告
    if (data.report) {
        // Notion rich_text limit, truncate
        props['备注'] = { rich_text: [{ text: { content: data.report.slice(0, 2000) } }] };
    }
    
    return props;
}

async function main() {
    const tasksDir = path.join(__dirname, 'tasks');
    let totalSynced = 0;
    let totalUpdated = 0;
    
    for (const dateStr of DATES) {
        const dateDir = path.join(tasksDir, dateStr, 'data');
        if (!fs.existsSync(dateDir)) {
            console.log(dateStr + ': 无data目录, 跳过');
            continue;
        }
        
        const dirs = fs.readdirSync(dateDir).filter(d => d.startsWith('match'));
        console.log(dateStr + ': ' + dirs.length + '个match目录');
        
        // Query existing Notion records
        const existing = await queryNotion(dateStr);
        const existingNames = new Set();
        for (const p of existing) {
            const n = p.properties.Name?.title?.[0]?.plain_text || '';
            if (!n.includes('分组统计')) existingNames.add(p);
        }
        
        for (const d of dirs) {
            const matchDir = path.join(dateDir, d);
            const data = readMatchData(matchDir);
            if (!data.matchnum) continue;
            
            const matchNum = data.matchnum;
            const props = buildNotionProps(matchNum, data, dateStr);
            
            // Check if this match already exists in Notion
            const existingPage = existingNames.find(p => {
                const n = p.properties.Name?.title?.[0]?.plain_text || '';
                return n.startsWith(matchNum);
            });
            
            if (existingPage) {
                // Update existing record
                await updatePage(existingPage.id, props);
                totalUpdated++;
                console.log('  📝 ' + matchNum + ' 已更新');
            } else {
                // Add new record
                await addPage(props);
                totalSynced++;
                console.log('  ➕ ' + matchNum + ' 新增');
            }
        }
    }
    
    console.log('\n完成! 新增:' + totalSynced + ', 更新:' + totalUpdated);
}

main().catch(e => console.error(e));
