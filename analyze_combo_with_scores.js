const https = require('https');
const fs = require('fs');

// 从zgzcw.com获取开奖结果
function fetchScores() {
    return new Promise((resolve) => {
        const req = https.request({
            hostname: 'cp.zgzcw.com',
            path: '/dc/getKaijiangFootBall.action',
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://cp.zgzcw.com/'
            },
            timeout: 15000
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(d));
        });
        req.on('error', () => resolve(''));
        req.on('timeout', () => { req.destroy(); resolve(''); });
        req.end();
    });
}

async function main() {
    console.log('从zgzcw.com获取开奖结果...');
    const html = await fetchScores();
    
    // 解析比分
    const scoreMap = {};
    const rows = html.match(/<tr[^>]*>(.*?)<\/tr>/gs) || [];
    
    for (const row of rows) {
        // 提取竞彩编号
        const numMatch = row.match(/(周[一二三四五六日]\d+)/);
        if (!numMatch) continue;
        const matchNum = numMatch[1];
        
        // 提取比分: "1:1 (1:0)"
        const scoreMatch = row.match(/(\d{1,2})[：:](\d{1,2})\s*\(\d{1,2}[：:]\d{1,2}\)/);
        if (!scoreMatch) continue;
        
        const homeScore = parseInt(scoreMatch[1]);
        const awayScore = parseInt(scoreMatch[2]);
        scoreMap[matchNum] = `${homeScore}:${awayScore}`;
    }
    
    console.log(`获取到 ${Object.keys(scoreMap).length} 场比分`);
    for (const [k, v] of Object.entries(scoreMap).sort()) {
        console.log(`  ${k}: ${v}`);
    }
    
    // 写入meta.json
    const path = require('path');
    const BASE = path.join(__dirname, 'tasks');
    let updated = 0;
    
    for (const d of fs.readdirSync(BASE).sort()) {
        const dp = path.join(BASE, d);
        if (!fs.statSync(dp).isDirectory()) continue;
        const dataDir = path.join(dp, 'data');
        if (!fs.existsSync(dataDir)) continue;
        
        let dateUpdated = 0;
        for (const m of fs.readdirSync(dataDir).sort()) {
            if (!m.startsWith('match')) continue;
            const metaPath = path.join(dataDir, m, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const matchnum = meta.matchnum || '';
            
            if (scoreMap[matchnum]) {
                meta.score = scoreMap[matchnum];
                fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
                updated++;
                dateUpdated++;
            }
        }
        if (dateUpdated > 0) console.log(`  ${d}: 更新${dateUpdated}场`);
    }
    
    console.log(`\n总更新: ${updated}场`);
    
    // 重新跑组合分析
    console.log('\n重新跑组合分析...');
    
    const records = [];
    let total = 0;
    
    for (const d of fs.readdirSync(BASE).sort()) {
        const dp = path.join(BASE, d);
        if (!fs.statSync(dp).isDirectory()) continue;
        const dataDir = path.join(dp, 'data');
        if (!fs.existsSync(dataDir)) continue;
        
        for (const m of fs.readdirSync(dataDir).sort()) {
            if (!m.startsWith('match')) continue;
            const mPath = path.join(dataDir, m);
            if (!fs.statSync(mPath).isDirectory()) continue;
            
            const metaPath = path.join(mPath, 'meta.json');
            const s26Path = path.join(mPath, 'step26_profit_ratio.json');
            if (!fs.existsSync(metaPath) || !fs.existsSync(s26Path)) continue;
            
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const s26 = JSON.parse(fs.readFileSync(s26Path, 'utf8'));
            
            total++;
            const macauLine = meta.macau_line || '';
            if (!macauLine) continue;
            
            const score = meta.score || '';
            if (!score || !score.includes(':')) continue;
            
            const parts = score.split(':');
            const home = parseInt(parts[0]);
            const away = parseInt(parts[1]);
            let actual;
            if (home > away) actual = '胜';
            else if (home === away) actual = '平';
            else actual = '负';
            
            const league = meta.league || '';
            
            const p = s26.profit_data || {};
            const winDir = p['主胜']?.profit_dir;
            const drawDir = p['平局']?.profit_dir;
            const loseDir = p['客胜']?.profit_dir;
            
            if (winDir === undefined) continue;
            
            const winLabel = winDir ? '赢' : '亏';
            const drawLabel = drawDir ? '赢' : '亏';
            const loseLabel = loseDir ? '赢' : '亏';
            const combo = `胜${winLabel}平${drawLabel}负${loseLabel}`;
            
            records.push({ macau: macauLine, league, combo, actual });
        }
    }
    
    console.log(`有效数据: ${records.length}场 (总${total}场)`);
    
    // 分析: 盘口 × 盈亏组合 → 胜平负概率
    const comboGroups = {};
    for (const r of records) {
        const key = `${r.macau}|${r.combo}`;
        if (!comboGroups[key]) comboGroups[key] = { count: 0, 胜: 0, 平: 0, 负: 0 };
        comboGroups[key].count++;
        comboGroups[key][r.actual]++;
    }
    
    // 联赛 × 盈亏组合
    const leagueCombo = {};
    for (const r of records) {
        const key = `${r.league}|${r.combo}`;
        if (!leagueCombo[key]) leagueCombo[key] = { count: 0, 胜: 0, 平: 0, 负: 0 };
        leagueCombo[key].count++;
        leagueCombo[key][r.actual]++;
    }
    
    // 三维度
    const tri = {};
    for (const r of records) {
        const key = `${r.macau}|${r.league}|${r.combo}`;
        if (!tri[key]) tri[key] = { count: 0, 胜: 0, 平: 0, 负: 0 };
        tri[key].count++;
        tri[key][r.actual]++;
    }
    
    // 输出报告
    console.log('\n' + '='.repeat(120));
    console.log('澳门即时盘 × 盈亏组合 → 胜平负概率 (样本≥3)');
    console.log('='.repeat(120));
    
    console.log('\n盘口              | 盈亏组合           | 场次 |  胜(%) |  平(%) |  负(%) | 最大概率');
    console.log('-'.repeat(120));
    
    const macauOrder = ['平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半', '球半',
                        '受平手/半球', '受半球', '受半球/一球', '受一球', '受一球/球半', '受球半'];
    
    let currentMacau = null;
    for (const macau of macauOrder) {
        for (const [key, v] of Object.entries(comboGroups)) {
            if (!key.startsWith(macau + '|') || v.count < 3) continue;
            const combo = key.split('|')[1];
            const winPct = v.胜 / v.count * 100;
            const drawPct = v.平 / v.count * 100;
            const losePct = v.负 / v.count * 100;
            
            const probs = [['胜', winPct], ['平', drawPct], ['负', losePct]];
            const [maxDir, maxPct] = probs.reduce((a, b) => a[1] > b[1] ? a : b);
            
            const sig = [];
            if (winPct >= 70) sig.push('胜↑');
            if (losePct >= 70) sig.push('负↑');
            if (drawPct <= 15) sig.push('平↓');
            const sigStr = sig.join(',');
            
            const prefix = currentMacau !== macau ? macau : '';
            currentMacau = macau;
            
            console.log(`${prefix.padEnd(18)} | ${combo.padEnd(16)} | ${String(v.count).padStart(4)} | ${(winPct+'%').padStart(6)} | ${(drawPct+'%').padStart(6)} | ${(losePct+'%').padStart(6)} | ${maxDir}(${maxPct.toFixed(0)}%) ${sigStr}`);
        }
    }
    
    // 联赛分组
    console.log('\n' + '\n' + '='.repeat(120));
    console.log('联赛 × 盈亏组合 → 胜平负概率 (样本≥3)');
    console.log('='.repeat(120));
    
    console.log('\n联赛            | 盈亏组合           | 场次 |  胜(%) |  平(%) |  负(%) | 最大概率');
    console.log('-'.repeat(120));
    
    const leagueTotals = {};
    for (const [key, v] of Object.entries(leagueCombo)) {
        const league = key.split('|')[0];
        leagueTotals[league] = (leagueTotals[league] || 0) + v.count;
    }
    const sortedLeagues = Object.entries(leagueTotals).sort((a, b) => b[1] - a[1]).map(x => x[0]);
    
    for (const league of sortedLeagues.slice(0, 10)) {
        for (const [key, v] of Object.entries(leagueCombo)) {
            if (!key.startsWith(league + '|') || v.count < 3) continue;
            const combo = key.split('|')[1];
            const winPct = v.胜 / v.count * 100;
            const drawPct = v.平 / v.count * 100;
            const losePct = v.负 / v.count * 100;
            
            const probs = [['胜', winPct], ['平', drawPct], ['负', losePct]];
            const [maxDir, maxPct] = probs.reduce((a, b) => a[1] > b[1] ? a : b);
            
            const sig = [];
            if (winPct >= 70) sig.push('胜↑');
            if (losePct >= 70) sig.push('负↑');
            if (drawPct <= 15) sig.push('平↓');
            const sigStr = sig.join(',');
            
            console.log(`${league.padEnd(14)} | ${combo.padEnd(16)} | ${String(v.count).padStart(4)} | ${(winPct+'%').padStart(6)} | ${(drawPct+'%').padStart(6)} | ${(losePct+'%').padStart(6)} | ${maxDir}(${maxPct.toFixed(0)}%) ${sigStr}`);
        }
    }
    
    // 三维度
    console.log('\n' + '\n' + '='.repeat(120));
    console.log('盘口 × 联赛 × 盈亏组合 (样本≥2)');
    console.log('='.repeat(120));
    
    console.log('\n盘口              | 联赛            | 盈亏组合           | 场次 |  胜(%) |  平(%) |  负(%) | 最大概率');
    console.log('-'.repeat(120));
    
    const triFiltered = Object.entries(tri).filter(([, v]) => v.count >= 2).sort((a, b) => b[1].count - a[1].count);
    
    for (const [key, v] of triFiltered.slice(0, 30)) {
        const [macau, league, combo] = key.split('|');
        const winPct = v.胜 / v.count * 100;
        const drawPct = v.平 / v.count * 100;
        const losePct = v.负 / v.count * 100;
        
        const probs = [['胜', winPct], ['平', drawPct], ['负', losePct]];
        const [maxDir, maxPct] = probs.reduce((a, b) => a[1] > b[1] ? a : b);
        
        const sig = [];
        if (winPct >= 70) sig.push('胜↑');
        if (losePct >= 70) sig.push('负↑');
        if (drawPct <= 15) sig.push('平↓');
        const sigStr = sig.join(',');
        
        console.log(`${macau.padEnd(18)} | ${league.padEnd(14)} | ${combo.padEnd(16)} | ${String(v.count).padStart(4)} | ${(winPct+'%').padStart(6)} | ${(drawPct+'%').padStart(6)} | ${(losePct+'%').padStart(6)} | ${maxDir}(${maxPct.toFixed(0)}%) ${sigStr}`);
    }
    
    // 保存JSON
    const output = {
        元信息: { 总场次: total, 有效场次: records.length, 有比分: records.length },
        盘口_盈亏组合_胜平负: comboGroups,
        联赛_盈亏组合_胜平负: leagueCombo,
        三维度_盘口_联赛_组合_胜平负: tri,
    };
    
    fs.writeFileSync('jingcai/analysis_macau_combo_league_with_scores.json', JSON.stringify(output, null, 2), 'utf8');
    console.log(`\n完整JSON已保存: jingcai/analysis_macau_combo_league_with_scores.json`);
}

main().catch(console.error);
