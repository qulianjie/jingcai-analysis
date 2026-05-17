// Feedback: update yesterday's match results in Notion
const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = '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';
const DS_ID = '463d8f65-411c-480d-bcc9-e16c4715497c';

// Actual results from zgzcw.com for Saturday matches played on May 2-3
// Based on web fetch from zgzcw
const actualResults = {
    '026': { score: '1:1', result: '平' },  // 尼斯 vs 朗斯
    '027': { score: '1:2', result: '负' },  // 奥萨苏纳 vs 巴塞罗那
    '028': { score: '0:0', result: '平' },  // 亚特兰大 vs 热那亚
    // May 2 matches that are still pending (not finished yet or results not available)
    // The remaining 45 matches from May 2 (001-025) may be different schedule
};

function notionRequest(method, urlPath, body) {
    return new Promise((resolve, reject) => {
        const data = body ? JSON.stringify(body) : null;
        const opts = {
            hostname: 'api.notion.com',
            path: urlPath,
            method: method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json'
            },
            timeout: 30000
        };
        if (data) opts.headers['Content-Length'] = Buffer.byteLength(data);
        const req = https.request(opts, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try { resolve(JSON.parse(d)); }
                catch(e) { resolve({ raw: d }); }
            });
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
        if (data) req.write(data);
        req.end();
    });
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function main() {
    console.log('\n📋 竞彩反馈机制 - 2026-05-02\n');
    
    // Query data source for May 2 matches
    console.log('[1/3] 查询 Notion 中 5月2日的比赛记录...');
    const all = await notionRequest('POST', '/v1/data_sources/' + DS_ID + '/query', {
        page_size: 100,
        filter: {
            property: '比赛日期',
            date: { equals: '2026-05-02' }
        }
    });
    
    const pages = all.results || [];
    console.log(`找到 ${pages.length} 场比赛\n`);
    
    if (pages.length === 0) {
        console.log('⚠️ Notion 中未找到 5月2日的比赛记录');
        console.log('提示：昨天的数据可能已被清理，或未同步');
        
        // Also check if any entries exist at all
        const allEntries = await notionRequest('POST', '/v1/data_sources/' + DS_ID + '/query', {
            page_size: 10
        });
        console.log(`数据库中共 ${allEntries.results?.length || 0} 条记录`);
        return;
    }
    
    // Get local predictions
    console.log('[2/3] 获取预测数据...');
    const taskDir = path.join(__dirname, 'tasks', '2026-05-02');
    const predictions = {};
    
    if (fs.existsSync(taskDir)) {
        const dirs = fs.readdirSync(taskDir).filter(f => {
            try {
                return fs.statSync(path.join(taskDir, f)).isDirectory();
            } catch { return false; }
        });
        
        for (const dir of dirs) {
            const metaPath = path.join(taskDir, dir, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            try {
                const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
                if (meta.matchnum) {
                    predictions[meta.matchnum] = {
                        prediction: meta.prediction || '',
                        confidence: meta.confidence || ''
                    };
                }
            } catch(e) {}
        }
    }
    console.log(`本地预测数据: ${Object.keys(predictions).length} 场\n`);
    
    // Update with actual results
    console.log('[3/3] 更新 Notion 反馈...\n');
    
    let updated = 0;
    let skipped = 0;
    let pending = 0;
    
    for (const page of pages) {
        const props = page.properties || {};
        const matchNum = props['竞彩编号']?.rich_text?.[0]?.plain_text || '';
        const home = props['主队']?.rich_text?.[0]?.plain_text || '';
        const away = props['客队']?.rich_text?.[0]?.plain_text || '';
        
        // Skip if already has feedback
        const existingScore = props['实际比分']?.rich_text?.[0]?.plain_text;
        if (existingScore) {
            console.log(`⏭️  ${matchNum} ${home} vs ${away} - 已有反馈`);
            skipped++;
            continue;
        }
        
        const predInfo = predictions[matchNum] || {};
        const actual = actualResults[matchNum];
        
        if (actual) {
            // Update with result
            const isCorrect = predInfo.prediction ? 
                predInfo.prediction.includes(actual.result) : null;
            
            await notionRequest('PATCH', '/v1/pages/' + page.id, {
                properties: {
                    '实际比分': { rich_text: [{ text: { content: actual.score } }] },
                    '实际结果': { select: { name: actual.result } },
                    '预测正确': { checkbox: isCorrect === true },
                    '反馈日期': { date: { start: '2026-05-03' } },
                    '反馈总结': { rich_text: [{ text: { content: `实际比分 ${actual.score}，竞彩结果 ${actual.result}${isCorrect !== null ? '，预测' + (isCorrect ? '正确' : '错误') : ''}` } }] }
                }
            });
            
            const predText = predInfo.prediction || '无预测';
            console.log(`✅ ${matchNum} ${home} vs ${away} | 预测: ${predText} | 实际: ${actual.score} (${actual.result}) | ${isCorrect ? '✓' : '✗'}`);
            updated++;
        } else {
            console.log(`⏳ ${matchNum} ${home} vs ${away} - 赛果尚未公布`);
            pending++;
        }
        
        await sleep(300);
    }
    
    console.log(`\n=== 反馈统计 ===`);
    console.log(`已更新: ${updated}`);
    console.log(`已跳过: ${skipped}`);
    console.log(`待查: ${pending}`);
    
    // Save log
    const logFile = path.join(__dirname, `feedback_2026-05-02.json`);
    fs.writeFileSync(logFile, JSON.stringify({
        date: '2026-05-02',
        total: pages.length,
        updated,
        skipped,
        pending,
        timestamp: new Date().toISOString()
    }, null, 2), 'utf8');
    console.log(`\n📄 日志已保存: ${logFile}`);
}

main().catch(e => {
    console.error('[FATAL]', e.message);
    process.exit(1);
});
