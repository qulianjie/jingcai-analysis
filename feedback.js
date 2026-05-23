const https = require('https');
const iconv = require('iconv-lite');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const log = require('./_log_util.js');
log.setLogDir(path.join(__dirname, 'tasks', new Date().toISOString().slice(0,10), 'logs'));


const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const DATA_DIR = path.join(__dirname, '..', 'data', 'jingcai');

if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

// ===== 获取终盘赔率数据（从step文件提取即时赔率） =====
function fetchFinalOdds(dateStr) {
    const odds = {};
    const taskDir = path.join(__dirname, 'tasks', dateStr);
    const dataDir = path.join(taskDir, 'data');
    
    // 先尝试从match目录读取（新流水线）
    let matchDirs = [];
    if (fs.existsSync(dataDir)) {
        matchDirs = fs.readdirSync(dataDir).filter(d => {
            const dp = path.join(dataDir, d);
            return fs.existsSync(dp) && fs.statSync(dp).isDirectory() && d.startsWith('match');
        });
    }
    console.log(`[终盘] 找到 ${matchDirs.length} 个比赛目录`);
    
    // 如果没有match目录，从matches_data.json读取FID（兼容旧流水线）
    if (matchDirs.length === 0) {
        const mdPath = path.join(taskDir, 'matches_data.json');
        if (fs.existsSync(mdPath)) {
            try {
                const md = JSON.parse(fs.readFileSync(mdPath, 'utf8'));
                const groups = md.groups || {};
                const tempDir = path.join(dataDir || path.join(taskDir, 'data'), '_tmp_odds');
                if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });
                
                for (const [gn, gd] of Object.entries(groups)) {
                    const ml = gd.matches || [];
                    for (const m of ml) {
                        const mn = m.matchnum || '';
                        const fid = m.fid || '';
                        const league = m.league || '';
                        const home = m.home || '';
                        const away = m.away || '';
                        if (!fid) continue;
                        
                        const mDir = path.join(tempDir, mn);
                        if (!fs.existsSync(mDir)) fs.mkdirSync(mDir, { recursive: true });
                        // 写meta.json让step146可以用match_dir模式
                        const meta = { matchnum: mn, fid, league, home, away, rq: m.rq || '' };
                        fs.writeFileSync(path.join(mDir, 'meta.json'), JSON.stringify(meta, null, 2), 'utf8');
                        
                        console.log(`[终盘] ${mn}(FID:${fid}) 获取终盘赔率...`);
                        try {
                            const r = execSync(`python step146_extractor.py "${mDir}"`, { cwd: __dirname, timeout: 60000, stdio: 'pipe' });
                            // 读取step1取live odds
                            const s1Path = path.join(mDir, 'group01_europe', 'step1_europe_base.txt');
                            const s4Path = path.join(mDir, 'group02_handicap', 'step4_handicap_base.txt');
                            if (fs.existsSync(s1Path)) {
                                const c1 = fs.readFileSync(s1Path, 'utf8');
                                const lines1 = c1.split('\n');
                                for (const line of lines1) {
                                    if (!line.includes('|')) continue;
                                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                                    if (parts.length < 8) continue;
                                    if (parts[0] === '竞彩官方' && parts[1] !== '-1') {
                                        odds[mn] = {
                                            jc_win: parseFloat(parts[4]), jc_draw: parseFloat(parts[5]), jc_loss: parseFloat(parts[6]),
                                        };
                                    }
                                    if (parts[0] === '百家平均') {
                                        if (!odds[mn]) odds[mn] = {};
                                        odds[mn].bj_win = parseFloat(parts[4]); odds[mn].bj_draw = parseFloat(parts[5]); odds[mn].bj_loss = parseFloat(parts[6]);
                                    }
                                    if (parts[0] === 'Interwetten') {
                                        if (!odds[mn]) odds[mn] = {};
                                        odds[mn].iw_win = parseFloat(parts[4]); odds[mn].iw_draw = parseFloat(parts[5]); odds[mn].iw_loss = parseFloat(parts[6]);
                                    }
                                }
                            }
                            if (fs.existsSync(s4Path)) {
                                const c4 = fs.readFileSync(s4Path, 'utf8');
                                for (const line of c4.split('\n')) {
                                    if (!line.includes('竞彩官方')) continue;
                                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                                    if (parts.length >= 8) {
                                        if (!odds[mn]) odds[mn] = {};
                                        odds[mn].rq_win = parseFloat(parts[5]); odds[mn].rq_draw = parseFloat(parts[6]); odds[mn].rq_loss = parseFloat(parts[7]);
                                    }
                                    break;
                                }
                            }
                        } catch(e) {
                            console.log(`[终盘] ${mn} 获取失败: ${e.message.substring(0,60)}`);
                        }
                    }
                }
                // 清理临时目录
                try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch(e) {}
            } catch(e) {
                console.log('[终盘] matches_data.json 解析失败:', e.message.substring(0,60));
            }
        } else {
            console.log('[终盘] 没有matches_data.json，无法获取终盘赔率');
        }
        return odds;
    }
    
    for (const dir of matchDirs) {
        try {
            const metaPath = path.join(dataDir, dir, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const matchNum = meta.matchnum || '';
            if (!matchNum) continue;
            
            const fid = meta.fid || '';
            const league = meta.league || '';
            const home = meta.home || '';
            const away = meta.away || '';
            
            if (!fid) continue;
            
            // 重新运行 step146_extractor.py 获取最新数据
            const matchDir = path.join(dataDir, dir);
            const step1Path = path.join(matchDir, 'group01_europe', 'step1_europe_base.txt');
            const step4Path = path.join(matchDir, 'group02_handicap', 'step4_handicap_base.txt');
            const step6Path = path.join(matchDir, 'group03_asian', 'step6_asian_base.txt');
            
            console.log(`[终盘] ${matchNum} 重新获取 step1/4/6 数据 (FID:${fid})...`);
            try {
                // 用 match_dir 模式调用，step146 自动从 meta.json 读取 fid/league
                execSync(`python step146_extractor.py "${matchDir}"`, {
                    cwd: __dirname,
                    timeout: 60000,
                    stdio: 'pipe'
                });
            } catch (e) {
                console.log(`[终盘] ${matchNum} step146 提取失败: ${e.message}`);
            }
            
            const o = {};
            
            // 1. step1_europe_base.txt - 欧赔基础（竞彩/百家/IW）
            if (fs.existsSync(step1Path)) {
                const c1 = fs.readFileSync(step1Path, 'utf8');
                const lines1 = c1.split('\n');
                for (const line of lines1) {
                    if (!line.includes('|')) continue;
                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                    if (parts.length < 8) continue;
                    
                    const keepArrow = (a) => { if (!a || a.length < 3) return ''; return a.slice(0,3); };                    // 竞彩官方: | 竞彩官方 | 初胜 | 初平 | 初负 | 即胜 | 即平 | 即负 | 变化 |
                    if (parts[0] === '竞彩官方' && parts[1] !== '-1') {
                        o.jc_win = Math.floor(parseFloat(parts[4]) * 10) / 10;
                        o.jc_draw = Math.floor(parseFloat(parts[5]) * 10) / 10;
                        o.jc_loss = Math.floor(parseFloat(parts[6]) * 10) / 10;
                        o.jc_panlu = keepArrow(parts[7]);
                    }
                    // Interwetten
                    if (parts[0] === 'Interwetten') {
                        o.iw_win = Math.floor(parseFloat(parts[4]) * 10) / 10;
                        o.iw_draw = Math.floor(parseFloat(parts[5]) * 10) / 10;
                        o.iw_loss = Math.floor(parseFloat(parts[6]) * 10) / 10;
                        o.iw_panlu = keepArrow(parts[7]);
                    }
                    // 百家平均
                    if (parts[0] === '百家平均') {
                        o.bj_win = Math.floor(parseFloat(parts[4]) * 10) / 10;
                        o.bj_draw = Math.floor(parseFloat(parts[5]) * 10) / 10;
                        o.bj_loss = Math.floor(parseFloat(parts[6]) * 10) / 10;
                        o.bj_panlu = keepArrow(parts[7]);
                    }
                }
            }
            
            // 2. step4_handicap_base.txt - 让球基础
            if (fs.existsSync(step4Path)) {
                const c4 = fs.readFileSync(step4Path, 'utf8');
                const lines4 = c4.split('\n');
                for (const line of lines4) {
                    if (!line.includes('|')) continue;
                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                    if (parts.length < 8) continue;
                    // | 竞彩官方 | 让球 | 初胜 | 初平 | 初负 | 即胜 | 即平 | 即负 |
                    if (parts[0] === '竞彩官方') {
                        o.rq_win = Math.floor(parseFloat(parts[5]) * 10) / 10;
                        o.rq_draw = Math.floor(parseFloat(parts[6]) * 10) / 10;
                        o.rq_loss = Math.floor(parseFloat(parts[7]) * 10) / 10;
                    }
                }
            }
            
            // 让球指数盘路（从step4数值计算初盘vs即时）
            if (odds[matchNum] && odds[matchNum].rq_win) {
                try {
                    const c4b = fs.readFileSync(step4Path, 'utf8');
                    const lines4b = c4b.split('\n');
                    for (const l4 of lines4b) {
                        if (!l4.includes('|')) continue;
                        const p4 = l4.split('|').map(x => x.trim()).filter(x => x);
                        if (p4.length < 8) continue;
                        if (p4[0] === '竞彩官方') {
                            const cmp = (a, b) => parseFloat(a) > parseFloat(b) ? '⬆' : parseFloat(a) < parseFloat(b) ? '⬇' : '➡';
                            odds[matchNum].rq_panlu = cmp(p4[2], p4[5]) + cmp(p4[3], p4[6]) + cmp(p4[4], p4[7]);
                        }
                    }
                } catch(e) {}
            }
            // 3. 澳门亚盘 - 从step6文件提取即时盘盘口文字
            if (fs.existsSync(step6Path)) {
                const c6 = fs.readFileSync(step6Path, 'utf8');
                const lines6 = c6.split('\n');
                for (const line of lines6) {
                    if (!line.includes('澳门')) continue;
                    // step6新格式: | 澳门 | 两球半（主水0.860|客水0.980） | 两球半（主水0.960|客水0.880） |
                    // 策略：去掉所有（主水...|客水...）再按|分割取第3段
                    const noBracket = line.replace(/[（(].*?[）)]/g, '');
                    const parts = noBracket.split('|').map(p => p.trim()).filter(p => p);
                    // 新格式: 去掉括号后 = | 澳门 | 两球半  | 两球半  |
                    // parts[0]=澳门, parts[1]=两球半, parts[2]=两球半
                    if (parts.length >= 3 && /[一-龥]/.test(parts[2])) {
                        o.macau = parts[2].replace(/[⬆⬇➡▽△↑↓→←↔]/g, '').trim();
                    } else if (parts.length >= 3) {
                        // 旧格式兼容: parts = [澳门, 05, 1.020, 0.940, 0.840]
                        // parts倒数第二个带箭头（如 0.940⬆➡），去掉数字和箭头
                        const raw = parts[parts.length - 2] || '';
                        o.macau = raw.replace(/[\d\.⬆⬇➡▽△↑↓→←↔]/g, '').trim();
                    }
                    break;
                }
            }
            // 如果step6没取到，从meta.json macau_line fallback
            if (!o.macau && fs.existsSync(metaPath)) {
                try {
                    const metaUpdated = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
                    if (metaUpdated.macau_line) {
                        o.macau = metaUpdated.macau_line.replace(/[⬆⬇➡▽△↑↓→←↔]/g, '').trim();
                    }
                } catch(e) {}
            }
            
            if (Object.keys(o).length > 0) {
                odds[matchNum] = o;
            }
        } catch (e) {}
    }
    
    console.log(`[终盘] 提取到 ${Object.keys(odds).length} 场赔率`);
    return odds;
}

// ===== 获取比赛结果 =====
// 数据源：500.com 竞彩页面（已完成的比赛在 td-team 中内嵌比分 如 "拉赫蒂1:1瓦萨"）
// ===== 获取比赛结果 =====
// 数据源：500.com 竞彩页面（已完成的比赛在 td-team 文本中内嵌比分）
async function fetchMatchResults(dateStr) {
    const results = {};
    
    return new Promise((resolve) => {
        const url = `https://trade.500.com/jczq/?playid=269&g=2&date=${dateStr}`;
        https.get(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            },
            timeout: 15000
        }, res => {
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => {
                try {
                    const raw = Buffer.concat(chunks);
                    const html = iconv.decode(raw, 'GBK');
                    
                    // 500.com交易页面，每场比赛一行 <tr data-matchnum="周四001" ...>
                    const trPattern = /<tr[^>]*class="[^"]*bet-tb-tr[^"]*"[^>]*>([\s\S]*?)<\/tr>/g;
                    let trMatch;
                    while ((trMatch = trPattern.exec(html)) !== null) {
                        const fullMatch = trMatch[0];
                        const mnMatch = fullMatch.match(/data-matchnum="([^"]+)"/);
                        if (!mnMatch) continue;
                        const matchNum = mnMatch[1].trim();
                        
                        // 队伍文本在 td-team 中（可能嵌套<a>标签）
                        const teamTD = trMatch[1].match(/<td[^>]*class="[^"]*td-team[^"]*"[^>]*>([\s\S]*?)<\/td>/);
                        if (!teamTD) continue;
                        const teamText = teamTD[1].replace(/<[^>]*>/g, '').trim();
                        
                        // 未完成比赛含 VS，完成比赛比分替换了 VS
                        if (teamText.indexOf('VS') === -1) {
                            const scoreMatch = teamText.match(/(\d+):(\d+)/);
                            if (scoreMatch) {
                                const hs = parseInt(scoreMatch[1]);
                                const as = parseInt(scoreMatch[2]);
                                if (hs <= 20 && as <= 20) {
                                    results[matchNum] = { homeScore: hs, awayScore: as };
                                }
                            }
                        }
                    }
                    
                    console.log(`[500] 获取到 ${Object.keys(results).length} 场比分（日期 ${dateStr}）`);
                } catch (e) {
                    console.log('[500] Parse error:', e.message);
                }
                resolve(results);
            });
        }).on('error', () => resolve(results));
    });
}

// ===== 查询 Notion 中已有的比赛记录 =====
function queryNotionMatches(dateStr) {
    const data = JSON.stringify({
        filter: {
            and: [
                {
                    property: '比赛日期',
                    date: { equals: dateStr }
                }
            ]
        },
        page_size: 100
    });

    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${DB_ID}/query`,
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(d));
                } catch (e) {
                    reject(new Error(`Parse error: ${d}`));
                }
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

function notionPatch(pageId, props) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ properties: props });
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/pages/${pageId}`,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                if (res.statusCode >= 400) reject(new Error(`HTTP ${res.statusCode}: ${d.slice(0,100)}`));
                else resolve();
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

// ===== 更新 Notion 页面 =====
function updateMatch(pageId, score, result, isCorrect, pred, handicap, rqPred, europeanOdds) {
    // 计算让球后结果
    const homeScore = parseInt(score.split(':')[0]) || 0;
    const awayScore = parseInt(score.split(':')[1]) || 0;
    const adjHome = homeScore - handicap;  // handicap>0=主队让X球
    let rqActualResult = '';
    if (adjHome > awayScore) rqActualResult = '胜';
    else if (adjHome < awayScore) rqActualResult = '负';
    else rqActualResult = '平';
    
    // 让球预测是否正确
    const predResult = predictionToResult(pred);
    let rqIsCorrect = null;
    if (rqPred && handicap !== 0) {
        const rqPredResult = predictionToResult(rqPred);
        rqIsCorrect = rqPredResult === rqActualResult;
    } else if (rqPred) {
        const rqPredResult = predictionToResult(rqPred);
        rqIsCorrect = rqPredResult === result;
    }
    
    // 构建让球文本
    let handicapText = '';
    if (handicap > 0) handicapText = `让${handicap}球`;
    else if (handicap < 0) handicapText = `受让${Math.abs(handicap)}球`;
    else handicapText = '平手';
    
    // 构建反馈总结
    const predCorrectMark = isCorrect ? '✅正确' : '❌错误';
    const rqCorrectMark = rqIsCorrect === true ? '✅正确' : (rqIsCorrect === false ? '❌错误' : '');
    // 安全过滤：替换&#xFFFD;乱码字符防止反馈总结带乱码
    const safe = s => s.replace(/\uFFFD/g, '');
    let summary = `竞彩预测: ${safe(pred)} → ${result} (${score}) ${predCorrectMark}`;
    if (rqPred) {
        const rqMark = rqCorrectMark ? ` ${rqCorrectMark}` : '';
        summary += `\n让球预测: ${safe(rqPred)} → ${handicapText} ${rqActualResult} (${adjHome}:${awayScore})${rqMark}`;
    }
    
    const props = {
        '实际比分': { rich_text: [{ text: { content: score || '' } }] },
        '实际结果': { rich_text: [{ text: { content: result || '' } }] },
        '反馈日期': { date: { start: new Date().toISOString().split('T')[0] } },
        '反馈总结': { rich_text: [{ text: { content: summary } }] },
        '预测正确': { checkbox: isCorrect },
    };
    
    // 添加终盘赔率数据（如果存在）
    if (europeanOdds) {
        // 竞彩欧赔
        if (europeanOdds.jc_win) props['终盘竞彩欧赔胜'] = { number: europeanOdds.jc_win };
        if (europeanOdds.jc_draw) props['终盘竞彩欧赔平'] = { number: europeanOdds.jc_draw };
        if (europeanOdds.jc_loss) props['终盘竞彩欧赔负'] = { number: europeanOdds.jc_loss };
        // 百家欧赔
        if (europeanOdds.bj_win) props['终盘百家欧赔胜'] = { number: europeanOdds.bj_win };
        if (europeanOdds.bj_draw) props['终盘百家欧赔平'] = { number: europeanOdds.bj_draw };
        if (europeanOdds.bj_loss) props['终盘百家欧赔负'] = { number: europeanOdds.bj_loss };
        // Interwetten
        if (europeanOdds.iw_win) props['终盘Interwetten胜'] = { number: europeanOdds.iw_win };
        if (europeanOdds.iw_draw) props['终盘Interwetten平'] = { number: europeanOdds.iw_draw };
        if (europeanOdds.iw_loss) props['终盘Interwetten负'] = { number: europeanOdds.iw_loss };
        // 让球指数
        if (europeanOdds.rq_win) props['终盘让球指数胜'] = { number: europeanOdds.rq_win };
        if (europeanOdds.rq_draw) props['终盘让球指数平'] = { number: europeanOdds.rq_draw };
        if (europeanOdds.rq_loss) props['终盘让球指数负'] = { number: europeanOdds.rq_loss };
        // 澳门亚盘
        if (europeanOdds.macau) props['终盘竞彩澳门亚盘'] = { rich_text: [{ text: { content: europeanOdds.macau } }] };
        // 盘路字段
        if (europeanOdds.jc_panlu) props['欧赔竞彩盘路'] = { rich_text: [{ text: { content: europeanOdds.jc_panlu } }] };
        if (europeanOdds.bj_panlu) props['欧赔百家盘路'] = { rich_text: [{ text: { content: europeanOdds.bj_panlu } }] };
        if (europeanOdds.iw_panlu) props['欧赔interwetten盘路'] = { rich_text: [{ text: { content: europeanOdds.iw_panlu } }] };
        if (europeanOdds.rq_panlu) props['让球指数盘路'] = { rich_text: [{ text: { content: europeanOdds.rq_panlu } }] };
        if (europeanOdds.macau_panlu) props['澳门亚盘盘路'] = { rich_text: [{ text: { content: europeanOdds.macau_panlu } }] };
    }
    
    if (rqPred) {
        props['让球预测'] = { rich_text: [{ text: { content: rqPred } }] };
    }

    if (rqIsCorrect !== null) {
        props['让球预测正确'] = { checkbox: rqIsCorrect };
    }

    const data = JSON.stringify({ properties: props });

    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/pages/${pageId}`,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                const parsed = JSON.parse(d);
                if (res.statusCode >= 400) {
                    reject(new Error(`HTTP ${res.statusCode}: ${d}`));
                } else {
                    resolve({ status: res.statusCode, data: parsed });
                }
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

// ===== 预测结果映射 =====
function predictionToResult(pred) {
    if (!pred) return null;
    // 处理让球预测格式（优先级最高）
    if (pred.includes('让球胜') || pred.includes('让球主胜')) return '胜';
    if (pred.includes('让球负') || pred.includes('让球客胜')) return '负';
    if (pred.includes('让球平')) return '平';
    // 处理简单格式
    if (pred.includes('主胜')) return '胜';
    if (pred.includes('客胜')) return '负';
    if (pred.includes('平局') || pred.includes('平')) return '平';
    // 兼容格式
    if (pred.includes('3')) return '胜';
    if (pred.includes('0')) return '负';
    if (pred.includes('1')) return '平';
    return null;
}

// ===== 分组统计 =====
function generateGroupStats(notionPages, matchResults, predictions) {
    const groups = {};
    
    for (const page of notionPages) {
        const props = page.properties;
        const nameField = props.Name?.title?.[0]?.plain_text || '';
        const nameMatch = nameField.match(/^([\u5468][\u4E00\u4E8C\u4E09\u56DB\u4E94\u516D\u65E5]\d+)/);
        const matchNum = nameMatch ? nameMatch[1] : '';
        
        // 获取竞彩预测
        const notionPred = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
        const predResult = predictionToResult(notionPred);
        
        // 获取步26_庄家最看好
        const zjText = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
        let zjResult = null;
        if (zjText.includes('主胜')) zjResult = '主胜';
        else if (zjText.includes('客胜')) zjResult = '客胜';
        else if (zjText.includes('平局')) zjResult = '平局';
        
        // 获取让球预测的方向（格式：受让1球 让球主胜 → "受让1球 主胜"）
        const rqPred = props['让球预测']?.rich_text?.[0]?.plain_text || '';
        let rqResult = null;
        // 提取让球数（受让X球 或 让X球）
        const rqNumMatch = rqPred.match(/(受让\d+球|让[+-]?\d+(?:\.5)?球|平手)/);
        const rqNumPart = rqNumMatch ? rqNumMatch[1] : '';
        // 提取方向
        if (rqPred.includes('让球主胜') || rqPred.includes('让球胜')) {
            rqResult = rqNumPart ? `${rqNumPart} 主胜` : '让球主胜';
        } else if (rqPred.includes('让球客胜')) {
            rqResult = rqNumPart ? `${rqNumPart} 客胜` : '让球客胜';
        } else if (rqPred.includes('让球平')) {
            rqResult = rqNumPart ? `${rqNumPart} 平` : '让球平';
        }
        
        // 获取实际结果
        const result = matchResults[matchNum];
        if (!result) continue;
        
        const score = `${result.homeScore}:${result.awayScore}`;
        let actualResult = '';
        if (result.homeScore > result.awayScore) actualResult = '胜';
        else if (result.homeScore < result.awayScore) actualResult = '负';
        else actualResult = '平';
        
        // 三维分组键：竞彩|庄家|让球（过滤掉没有预测的比赛）
        if (!predResult && !zjResult && !rqResult) continue; // 三个都没预测，跳过
        const groupKey = `${predResult || '未知'}|${zjResult || '未知'}|${rqResult || '未知'}`;
        
        if (!groups[groupKey]) {
            groups[groupKey] = { total: 0, 胜: 0, 平: 0, 负: 0 };
        }
        groups[groupKey].total++;
        groups[groupKey][actualResult]++;
    }
    
    return groups;
}

// ===== 创建Notion每日统计页面 =====
function createDailyStats(dateStr, groups) {
    const parentPageId = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71'; // match数据库父页面
    const dailyDbId = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9'; // 历史每日汇总数据库
    
    // 构建统计内容
    let content = `## 📊 ${dateStr}分组统计（按竞彩/庄家/让球分组）\n\n`;
    content += `| 竞彩 | 庄家 | 让球 | 场数 | 实际胜 | 实际平 | 实际负 |\n`;
    content += `|------|------|------|------|--------|--------|--------|\n`;
    
    const sortedGroups = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);
    
    for (const [key, stats] of sortedGroups) {
        const [pred, zj, rq] = key.split('|');
        content += `| ${pred} | ${zj} | ${rq} | ${stats.total} | ${stats.胜} | ${stats.平} | ${stats.负} |\n`;
    }
    
    // 计算总计
    let totalWins = 0, totalDraws = 0, totalLosses = 0;
    for (const stats of Object.values(groups)) {
        totalWins += stats.胜;
        totalDraws += stats.平;
        totalLosses += stats.负;
    }
    const total = totalWins + totalDraws + totalLosses;
    
    content += `\n**${total}场合计：胜${totalWins} 平${totalDraws} 负${totalLosses}**\n`;
    
    // 找出最大分组
    const maxGroup = sortedGroups[0];
    if (maxGroup) {
        const [key, stats] = maxGroup;
        const [pred, zj, rq] = key.split('|');
        content += `\n最大分组是「竞彩${pred} | 庄家${zj} | 让球${rq}」${stats.total}场，实际结果是胜${stats.胜}平${stats.平}负${stats.负}。\n`;
    }
    
    // 2. 先删除当天已有的每日汇总记录（避免重复）
    // 注：26步数据库已用于存储26步分析内容，分组统计不再写入该数据库
    // 如需保留分组统计功能，请创建独立的每日统计数据库
    console.log('[INFO] 跳过写入Notion（26步数据库已用于存储26步分析内容）');
    
    // 2a. 查询并删除当天已有记录
    function deleteDailyByDate() {
        return queryDailyDb().then(r => {
            const delPromises = [];
            for (const page of r.results) {
                const pageDate = page.properties['日期']?.title?.[0]?.plain_text || '';
                if (pageDate === dateStr) {
                    const delData = JSON.stringify({ archived: true });
                    delPromises.push(new Promise((resolve, reject) => {
                        const req = https.request({
                            hostname: 'api.notion.com',
                            path: `/v1/pages/${page.id}`,
                            method: 'PATCH',
                            headers: {
                                'Authorization': 'Bearer ' + API_KEY,
                                'Notion-Version': '2022-06-28',
                                'Content-Type': 'application/json'
                            }
                        }, res => { let dd = ''; res.on('data', c => dd += c); res.on('end', () => resolve()); });
                        req.on('error', reject);
                        req.write(delData);
                        req.end();
                    }));
                }
            }
            return Promise.all(delPromises);
        });
    }
    
    // 2b. 插入当天分组记录（替换旧的）
    for (const [key, stats] of sortedGroups) {
        const [pred, zj, rq] = key.split('|');
        
        const dailyDbData = JSON.stringify({
            parent: { database_id: dailyDbId },
            properties: {
                '日期': { title: [{ text: { content: dateStr } }] },
                '竞彩': { select: { name: pred } },
                '庄家': { select: { name: zj } },
                '让球': { select: { name: rq } },
                '场数': { number: stats.total },
                '胜': { number: stats.胜 },
                '平': { number: stats.平 },
                '负': { number: stats.负 }
            }
        });
        
        insertPromises.push(
            new Promise((resolve, reject) => {
                const req = https.request({
                    hostname: 'api.notion.com',
                    path: '/v1/pages',
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + API_KEY,
                        'Notion-Version': '2022-06-28',
                        'Content-Type': 'application/json'
                    }
                }, res => {
                    let d = '';
                    res.on('data', c => d += c);
                    res.on('end', () => {
                        try {
                            const result = JSON.parse(d);
                            if (res.statusCode >= 400) {
                                reject(new Error(`HTTP ${res.statusCode}: ${d}`));
                            } else {
                                resolve(result);
                            }
                        } catch (e) {
                            reject(new Error(`Parse error: ${d}`));
                        }
                    });
                });
                req.on('error', reject);
                req.write(dailyDbData);
                req.end();
            })
        );
    }
    
    // 3. 从历史每日汇总聚合到历史汇总
    const historyDbId = '35d91ad7-17ba-802f-acb7-ebfd74db132c';
    
    // 3a. 查询历史每日汇总所有记录
    function queryDailyDb() {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify({ page_size: 100 });
            const req = https.request({
                hostname: 'api.notion.com',
                path: `/v1/databases/${dailyDbId}/query`,
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + API_KEY,
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                }
            }, res => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => {
                    try { resolve(JSON.parse(d)); }
                    catch (e) { reject(new Error(`Parse: ${d}`)); }
                });
            });
            req.on('error', reject);
            req.write(data);
            req.end();
        });
    }
    
    // 3b. 清空目标数据库
    function clearHistoryDb() {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify({ page_size: 100 });
            const req = https.request({
                hostname: 'api.notion.com',
                path: `/v1/databases/${historyDbId}/query`,
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + API_KEY,
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                }
            }, res => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => {
                    try {
                        const r = JSON.parse(d);
                        if (r.results.length === 0) { resolve(); return; }
                        let archived = 0;
                        for (const page of r.results) {
                            const delData = JSON.stringify({ archived: true });
                            const delReq = https.request({
                                hostname: 'api.notion.com',
                                path: `/v1/pages/${page.id}`,
                                method: 'PATCH',
                                headers: {
                                    'Authorization': 'Bearer ' + API_KEY,
                                    'Notion-Version': '2022-06-28',
                                    'Content-Type': 'application/json'
                                }
                            }, delRes => {
                                let dd = '';
                                delRes.on('data', c => dd += c);
                                delRes.on('end', () => {
                                    archived++;
                                    if (archived === r.results.length) resolve();
                                });
                            });
                            delReq.write(delData);
                            delReq.end();
                        }
                    } catch (e) { reject(e); }
                });
            });
            req.on('error', reject);
            req.write(data);
            req.end();
        });
    }
    
    // 3c. 插入聚合数据
    function insertAgg(agg) {
        const entries = Object.entries(agg);
        return Promise.all(entries.map(([key, stats]) => {
            const [jp, zj, rq] = key.split('|');
            const data = JSON.stringify({
                parent: { database_id: historyDbId },
                properties: {
                    '竞彩': { title: [{ text: { content: jp } }] },
                    '庄家': { select: { name: zj } },
                    '让球': { select: { name: rq } },
                    '场数': { number: stats.total },
                    '胜': { number: stats.wins },
                    '平': { number: stats.draws },
                    '负': { number: stats.losses }
                }
            });
            return new Promise((resolve, reject) => {
                const req = https.request({
                    hostname: 'api.notion.com',
                    path: '/v1/pages',
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + API_KEY,
                        'Notion-Version': '2022-06-28',
                        'Content-Type': 'application/json'
                    }
                }, res => {
                    let d = '';
                    res.on('data', c => d += c);
                    res.on('end', () => resolve());
                });
                req.on('error', reject);
                req.write(data);
                req.end();
            });
        }));
    }
    
    // 1. 创建match数据库中的分组统计记录
    const matchPageData = JSON.stringify({
        parent: { database_id: DB_ID },
        properties: {
            'Name': { title: [{ text: { content: `${dateStr} 分组统计` } }] },
            '比赛日期': { date: { start: dateStr } }
        }
    });
    
    // 先删除当天已有的分组统计页面（从match数据库查询）
    function deleteOldDailyStats() {
        const queryData = JSON.stringify({
            filter: {
                and: [
                    { property: '比赛日期', date: { equals: dateStr } },
                    { property: 'Name', title: { contains: '分组统计' } }
                ]
            },
            page_size: 20
        });
        return new Promise((resolve, reject) => {
            const req = https.request({
                hostname: 'api.notion.com',
                path: `/v1/databases/${DB_ID}/query`,
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + API_KEY,
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                }
            }, res => {
                let d = '';
                res.on('data', c => d += c);
                res.on('end', () => {
                    try {
                        const r = JSON.parse(d);
                        const delPromises = (r.results || []).map(page => {
                            const delData = JSON.stringify({ archived: true });
                            return new Promise((resolve, reject) => {
                                const req = https.request({
                                    hostname: 'api.notion.com',
                                    path: `/v1/pages/${page.id}`,
                                    method: 'PATCH',
                                    headers: {
                                        'Authorization': 'Bearer ' + API_KEY,
                                        'Notion-Version': '2022-06-28',
                                        'Content-Type': 'application/json'
                                    }
                                }, res => { let dd = ''; res.on('data', c => dd += c); res.on('end', () => resolve()); });
                                req.on('error', reject);
                                req.write(delData);
                                req.end();
                            });
                        });
                        Promise.all(delPromises).then(resolve);
                    } catch (e) { reject(e); }
                });
            });
            req.on('error', reject);
            req.write(queryData);
            req.end();
        });
    }
    
    // 先删除旧记录，再插入新记录，然后聚合到历史汇总
    return deleteOldDailyStats()
        .then(() => deleteDailyByDate())
        .then(() => {
            // 插入新的分组统计页面 + 每日汇总记录
            return Promise.all([
                new Promise((resolve, reject) => {
                    const req = https.request({
                        hostname: 'api.notion.com',
                        path: '/v1/pages',
                        method: 'POST',
                        headers: {
                            'Authorization': 'Bearer ' + API_KEY,
                            'Notion-Version': '2022-06-28',
                            'Content-Type': 'application/json'
                        }
                    }, res => {
                        let d = '';
                        res.on('data', c => d += c);
                        res.on('end', () => {
                            try {
                                const result = JSON.parse(d);
                                if (res.statusCode >= 400) {
                                    reject(new Error(`HTTP ${res.statusCode}: ${d}`));
                                } else {
                                    resolve(result);
                                }
                            } catch (e) {
                                reject(new Error(`Parse error: ${d}`));
                            }
                        });
                    });
                    req.on('error', reject);
                    req.write(matchPageData);
                    req.end();
                }),
                ...insertPromises
            ]).then(() => {
                // 写入完成后，聚合到历史汇总
                return queryDailyDb().then(r => {
                    const agg = {};
                    for (const page of r.results) {
                        const props = page.properties;
                        const jp = props['竞彩']?.select?.name || '未知';
                        const zj = props['庄家']?.select?.name || '未知';
                        const rq = props['让球']?.select?.name || '未知';
                        const count = props['场数']?.number || 0;
                        const wins = props['胜']?.number || 0;
                        const draws = props['平']?.number || 0;
                        const losses = props['负']?.number || 0;
                        const key = `${jp}|${zj}|${rq}`;
                        if (!agg[key]) agg[key] = { total: 0, wins: 0, draws: 0, losses: 0 };
                        agg[key].total += count;
                        agg[key].wins += wins;
                        agg[key].draws += draws;
                        agg[key].losses += losses;
                    }
                    return clearHistoryDb().then(() => insertAgg(agg));
                });
            });
        });
}

// ===== 主流程 =====
async function main() {
    const args = process.argv.slice(2);
    let targetDate = null;
    
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--date' && i + 1 < args.length) {
            targetDate = args[i + 1];
        }
    }
    
    // 当传了 --date 时，处理前一天（已经开赛的比赛）
    if (targetDate) {
        const prevDay = new Date(targetDate);
        prevDay.setDate(prevDay.getDate() - 1);
        targetDate = prevDay.toISOString().split('T')[0];
    } else {
        // 默认昨天
        const yesterday = new Date(Date.now() - 86400000);
        targetDate = yesterday.toISOString().split('T')[0];
    }
    
    console.log(`\n📋 竞彩反馈机制 - ${targetDate}\n`);
    
    // 1. 查询 Notion 中的比赛
    console.log('[1/4] 查询 Notion 比赛记录...');
    const notionResult = await queryNotionMatches(targetDate);
    const notionPages = notionResult.results || [];
    
    if (notionPages.length === 0) {
        console.log(`⚠️ Notion 中未找到 ${targetDate} 的比赛记录`);
        console.log('提示: 请先运行竞彩流水线同步数据');
        return;
    }
    
    console.log(`找到 ${notionPages.length} 场比赛\n`);
    
    // 2. 获取实际赛果
    console.log('[2/4] 获取比赛结果...');
    
    // 从外部获取赛果
    const matchResults = await fetchMatchResults(targetDate);
    console.log(`获取到 ${Object.keys(matchResults).length} 场赛果`);
    
    // ==== 存档比分到本地永久快照（避免源站数据过期丢失）====
    const archiveFile = path.join(DATA_DIR, 'scores_archive.json');
    let archive = {};
    if (fs.existsSync(archiveFile)) {
        try { archive = JSON.parse(fs.readFileSync(archiveFile, 'utf8')); } catch(e) {}
    }
    if (Object.keys(matchResults).length > 0) {
        archive[targetDate] = matchResults;
        fs.writeFileSync(archiveFile, JSON.stringify(archive, null, 2), 'utf8');
        console.log(`📦 比分已存档: ${archiveFile} (${Object.keys(matchResults).length} 场)`);
    }
    
    // ==== 同时更新历史汇总：把前几天的比分也补上（如果源站还能拿到）====
    // 检查当前日期前后3天的存档是否完整，不完整时从当天的matchResults补充
    if (Object.keys(matchResults).length > 0) {
        const datesToPatch = {};
        // 目标日期本身已经更新了，不用补
        // 尝试补前一天和后一天的（如果当天抓到的比分实际属于其他日期）
        for (const [mn, rs] of Object.entries(matchResults)) {
            // matchResults key是比赛编号，不含日期，所以直接从当前targetDate推断
            // 不做额外操作，保持简单：只写当天的
        }
    }
    
    // 获取终盘赔率数据（从step文件提取即时赔率）
    const finalOdds = fetchFinalOdds(targetDate);
    console.log(`获取到 ${Object.keys(finalOdds).length} 场终盘赔率`);
    
    // 从本地任务目录读取报告文件获取预测信息
    const taskDir = path.join(__dirname, 'tasks', targetDate);
    const predictions = {};
    
    if (fs.existsSync(taskDir)) {
        const mdFiles = fs.readdirSync(taskDir).filter(f => f.endsWith('.md') && !f.startsWith('sunday'));
        for (const file of mdFiles) {
            const filePath = path.join(taskDir, file);
            try {
                const content = fs.readFileSync(filePath, 'utf8');
                const numMatch = file.match(/^([\u5468][\u4E00\u4E8C\u4E09\u56DB\u4E94\u516D\u65E5]\d+)[_]/);
                if (!numMatch) continue;
                const matchNum = numMatch[1];
                // 提取竞彩预测
                let pred = '';
                let m = content.match(/竞彩预测[:\s]*([^\n]+)/);
                if (m) pred = m[1].trim();
                if (!pred) {
                    m = content.match(/竞彩结论[:\s]*([^\n]+)/);
                    if (m) pred = m[1].trim();
                }
                if (!pred) {
                    m = content.match(/(?:推荐|建议)[:\s]*([^\n]+)/);
                    if (m) pred = m[1].trim();
                }
                // 提取让球预测
                let rqPred = '';
                m = content.match(/让球预测[:\s]*([^\n|]+)/);
                if (m) rqPred = m[1].trim();
                // 提取让球数(从让球预测文本解析，方向与rqPred一致)
                let handicap = 0;
                const isShouRang = rqPred.match(/受让(\d+(?:\.5)?)球/);
                const isRang = rqPred.match(/(?:^|[^受])让(\d+(?:\.5)?)球/);
                if (isShouRang) handicap = -parseFloat(isShouRang[1]);
                else if (isRang) handicap = parseFloat(isRang[1]);
                predictions[matchNum] = { prediction: pred, rqPred: rqPred, handicap: handicap };
            } catch (e) {}
        }
    }
    
    console.log(`本地预测数据: ${Object.keys(predictions).length} 场`);
    
    // 3. 更新 Notion
    console.log('\n[3/4] 更新 Notion 记录...\n');
    
    let updated = 0;
    let skipped = 0;
    
    for (const page of notionPages) {
        const props = page.properties;
        // Notion Name field: "周三007 欧冠 拜仁vs巴黎圣曼"
        const nameField = props.Name?.title?.[0]?.plain_text || '';
        const nameMatch = nameField.match(/^([\u5468][\u4E00\u4E8C\u4E09\u56DB\u4E94\u516D\u65E5]\d+)/);
        const matchNum = nameMatch ? nameMatch[1] : '';
        // Extract teams from Name: "周三007 欧冠 拜仁vs巴黎圣曼" -> "拜仁" vs "巴黎圣曼"
        const teamMatch = nameField.match(/\d+\s*\S+\s*(.+?)\s*vs\s*(.+)$/);
        const home = teamMatch ? teamMatch[1].trim() : '';
        const away = teamMatch ? teamMatch[2].trim() : '';
        // Prediction from Notion (竞彩预测 field)
        const notionPred = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
        
        // 检查是否已有终盘赔率数据
        const matchOdds = finalOdds[matchNum] || null;
        
        // 无论是否已有反馈，都重新生成总结（修复：老反馈总结可能数据错误）
        // 先补充终盘赔率
        if (matchOdds) {
            try {
                const oddProps = {};
                if (matchOdds.jc_win) oddProps['终盘竞彩欧赔胜'] = { number: matchOdds.jc_win };
                if (matchOdds.jc_draw) oddProps['终盘竞彩欧赔平'] = { number: matchOdds.jc_draw };
                if (matchOdds.jc_loss) oddProps['终盘竞彩欧赔负'] = { number: matchOdds.jc_loss };
                if (matchOdds.bj_win) oddProps['终盘百家欧赔胜'] = { number: matchOdds.bj_win };
                if (matchOdds.bj_draw) oddProps['终盘百家欧赔平'] = { number: matchOdds.bj_draw };
                if (matchOdds.bj_loss) oddProps['终盘百家欧赔负'] = { number: matchOdds.bj_loss };
                if (matchOdds.iw_win) oddProps['终盘Interwetten胜'] = { number: matchOdds.iw_win };
                if (matchOdds.iw_draw) oddProps['终盘Interwetten平'] = { number: matchOdds.iw_draw };
                if (matchOdds.iw_loss) oddProps['终盘Interwetten负'] = { number: matchOdds.iw_loss };
                if (matchOdds.rq_win) oddProps['终盘让球指数胜'] = { number: matchOdds.rq_win };
                if (matchOdds.rq_draw) oddProps['终盘让球指数平'] = { number: matchOdds.rq_draw };
                if (matchOdds.rq_loss) oddProps['终盘让球指数负'] = { number: matchOdds.rq_loss };
                if (matchOdds.macau) oddProps['终盘竞彩澳门亚盘'] = { rich_text: [{ text: { content: matchOdds.macau } }] };
                await notionPatch(page.id, oddProps);
            } catch(e) {}
        }
        
        // 获取预测（优先用Notion中的竞彩预测）
        const pred = notionPred || '';
        const predResult = predictionToResult(pred);
        
        // 获取让球预测（从Notion）
        const rqPred = props['让球预测']?.rich_text?.[0]?.plain_text || '';
        // 从让球预测文本直接提取让球数（不依赖本地文件解析，本地可能失败）
        let handicap = 0;
        if (rqPred) {
            const shou = rqPred.match(/受让(\d+(?:\.5)?)球/);
            const rang = rqPred.match(/(?:^|[^受])让(\d+(?:\.5)?)球/);
            if (shou) handicap = -parseFloat(shou[1]);
            else if (rang) handicap = parseFloat(rang[1]);
        }
        
        // 获取实际赛果
        const result = matchResults[matchNum];
        
        if (!result) {
            console.log(`📝 ${matchNum} ${home} vs ${away}`);
            console.log(`   预测: ${pred || '无'}`);
            console.log(`   状态: 等待赛果公布`);
            console.log('');
            continue;
        }
        
        // 计算结果
        const score = `${result.homeScore}:${result.awayScore}`;
        let actualResult = '';
        if (result.homeScore > result.awayScore) actualResult = '胜';
        else if (result.homeScore < result.awayScore) actualResult = '负';
        else actualResult = '平';
        
        const isCorrect = predResult === actualResult;
        
        console.log(`📝 ${matchNum} ${home} vs ${away}`);
        console.log(`   比分: ${score} (${actualResult})`);
        console.log(`   预测: ${pred} → ${predResult || '未知'}`);
        console.log(`   正确: ${isCorrect ? '✅' : '❌'}`);
        
        // 更新 Notion
        try {
            const matchFinalOdds = finalOdds[matchNum] || null;
            await updateMatch(page.id, score, actualResult, isCorrect, pred, handicap, rqPred, matchFinalOdds);
            console.log(`   ✅ 已更新 Notion`);
            if (matchFinalOdds) {
                console.log(`   终盘欧赔: ${matchFinalOdds.jc_win} / ${matchFinalOdds.jc_draw} / ${matchFinalOdds.jc_loss}`);
            }
            updated++;
        } catch (e) {
            console.log(`   ❌ 更新失败: ${e.message}`);
        }
        console.log('');
    }

    console.log(`\n✅ 反馈检查完成`);
    console.log(`   已更新: ${updated}`);
    console.log(`   已跳过: ${skipped}`);
    console.log(`   待查: ${notionPages.length - updated - skipped}`);
    
    // 4. 生成分组统计并写入Notion
    console.log('\n[4/5] 生成分组统计...');
    const groups = generateGroupStats(notionPages, matchResults, predictions);
    
    // 打印统计
    console.log('\n📊 分组统计:');
    const sortedGroups = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);
    for (const [key, stats] of sortedGroups) {
        const [pred, zj, rq] = key.split('|');
        console.log(`| ${pred} | ${zj} | ${rq} | ${stats.total} | ${stats.胜} | ${stats.平} | ${stats.负} |`);
    }
    
    // 计算总计
    let totalWins = 0, totalDraws = 0, totalLosses = 0;
    for (const stats of Object.values(groups)) {
        totalWins += stats.胜;
        totalDraws += stats.平;
        totalLosses += stats.负;
    }
    const total = totalWins + totalDraws + totalLosses;
    console.log(`\n${total}场合计：胜${totalWins} 平${totalDraws} 负${totalLosses}`);
    
    // 写入Notion（match页面 + 每日分组 + 聚合到历史汇总）
    try {
        // 跳过写入Notion（26步数据库已用于存储26步分析内容，分组统计不再写入）
        console.log('✅ match页面 + 每日分组 + 历史汇总 已跳过（26步数据库已用于存储26步分析内容）');
    } catch (e) {
        console.log(`❌ 写入Notion失败: ${e.message}`);
    }
    
    // 5. 全量刷新历史汇总（从竞彩比赛追踪明细重新汇总）
    try {
        console.log('\n[5/5] 全量刷新历史汇总...');
        const { execSync } = require('child_process');
        const result = execSync('node sync_summary.js', { cwd: __dirname, stdio: 'pipe', timeout: 300000 });
        const output = result.toString();
        // 只输出关键行
        const lines = output.split('\n');
        lines.filter(l => l.includes('✅') || l.includes('❌') || l.includes('总计') || l.includes('分组') || l.includes('清空') || l.includes('已写入') || l.includes('同步')).forEach(l => console.log(l));
        console.log('✅ 历史汇总已刷新');
    } catch (e) {
        console.log(`⚠️ 历史汇总刷新失败: ${e.message}`);
        if (e.stdout) {
            const out = e.stdout.toString();
            const keyLines = out.split('\n').filter(l => l.includes('❌') || l.includes('[FATAL]'));
            keyLines.forEach(l => console.log('  ' + l));
        }
    }

    // 保存反馈日志
    const logFile = path.join(DATA_DIR, `feedback_${targetDate}.json`);
    fs.writeFileSync(logFile, JSON.stringify({
        date: targetDate,
        total: notionPages.length,
        updated,
        skipped,
        pending: notionPages.length - updated - skipped,
        groups: Object.fromEntries(sortedGroups),
        timestamp: new Date().toISOString()
    }, null, 2), 'utf8');

    console.log(`\n📄 日志已保存: ${logFile}`);
}

main().catch(err => {
    console.error('[FATAL]', err.message);
    process.exit(1);
});
