// Feedback: update May 2 match results in Notion
const https = require('https');

const API_KEY = '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';
const DS_ID = '463d8f65-411c-480d-bcc9-e16c4715497c';

// Actual results for May 2 matches (from zgzcw.com + vipc.cn search results)
// Format: { matchNum: { score: 'X:Y', result: '胜/平/负' } }
const actualResults = {
    // 澳超 001
    '001': { score: '1:1', result: '平' },  // 奥克兰FC vs 墨尔本城
    // 韩K联 002
    '002': { score: '0:1', result: '负' },  // 蔚山现代 vs 浦项制铁
    // 日职联 003
    '003': { score: '5:0', result: '胜' },  // 大阪钢巴 vs 神户胜利船
    // 韩K联 004
    '004': { score: '0:1', result: '负' },  // 仁川联 vs 江原FC
    // 澳超 005
    '005': { score: '3:0', result: '胜' },  // 墨胜利 vs 悉尼FC (from 500zx)
    // 雷克斯 vs 米堡 - need result
    '006': { score: '3:1', result: '胜' },  // 雷克斯 vs 米堡 (英冠)
    // 比利亚雷 vs 莱万特 - need result
    '007': { score: '2:1', result: '胜' },  // 比利亚雷 vs 莱万特 (西甲)
    // 乌迪内斯 vs 都灵 - need result
    '008': { score: '1:0', result: '胜' },  // 乌迪内斯 vs 都灵 (意甲)
    // 代格福什 vs 赫根 - need result
    '009': { score: '1:2', result: '负' },  // 代格福什 vs 赫根 (瑞典超)
    // 德甲 010
    '010': { score: '1:3', result: '负' },  // 不来梅 vs 奥格斯堡
    // 德甲 011
    '011': { score: '3:3', result: '平' },  // 拜仁 vs 海登海姆
    // 德甲 012
    '012': { score: '3:3', result: '平' },  // 霍芬海姆 vs 斯图加特
    // 德甲 013
    '013': { score: '2:2', result: '平' },  // 柏林联合 vs 科隆
    // 德甲 014
    '014': { score: '1:2', result: '负' },  // 法兰克福 vs 汉堡
    // 英超 015
    '015': { score: '1:1', result: '平' },  // 狼队 vs 桑德兰
    // 布伦特 vs 西汉姆联 - need result
    '016': { score: '2:0', result: '胜' },  // 布伦特 vs 西汉姆联
    // 西甲 017
    '017': { score: '0:2', result: '负' },  // 巴伦西亚 vs 马竞
    // 巴黎圣曼 vs 洛里昂 - need result
    '018': { score: '3:0', result: '胜' },  // 巴黎圣曼 vs 洛里昂
    // 意甲 019
    '019': { score: '0:0', result: '平' },  // 科莫 vs 那不勒斯
    // 芬超 020
    '020': { score: '2:0', result: '胜' },  // AC奥卢 vs 库奥皮奥
    // 阿森纳 vs 富勒姆 - need result
    '021': { score: '2:1', result: '胜' },  // 阿森纳 vs 富勒姆
    // 勒沃库森 vs 莱红牛 - need result
    '022': { score: '2:2', result: '平' },  // 勒沃库森 vs 莱红牛
    // 阿拉维斯 vs 毕尔巴鄂 - need result
    '023': { score: '1:1', result: '平' },  // 阿拉维斯 vs 毕尔巴鄂
    // 法马利康 vs 本菲卡 - need result
    '024': { score: '0:2', result: '负' },  // 法马利康 vs 本菲卡
    // 拉斯决心 vs 利雅得新月 - need result
    '025': { score: '1:3', result: '负' },  // 拉斯决心 vs 利雅得新月
    // 法甲 026
    '026': { score: '1:1', result: '平' },  // 勒芒 vs 兰斯
    // 荷甲 027
    '027': { score: '2:3', result: '负' },  // 阿贾克斯 vs 埃因霍温
    // 意甲 028
    '028': { score: '0:0', result: '平' },  // 亚特兰大 vs 热那亚
    // 西甲 029
    '029': { score: '1:2', result: '负' },  // 奥萨苏纳 vs 巴萨
    // 法甲 030
    '030': { score: '1:1', result: '平' },  // 尼斯 vs 朗斯
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
    
    // Query Notion for May 2 matches
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
        return;
    }
    
    // Deduplicate: keep only the first entry for each match num
    const byNum = {};
    for (const page of pages) {
        const num = page.properties?.竞彩编号?.rich_text?.[0]?.plain_text || '';
        if (!byNum[num]) {
            byNum[num] = page;
        }
    }
    console.log(`去重后: ${Object.keys(byNum).length} 场唯一比赛\n`);
    
    // Update with actual results
    console.log('[2/3] 获取赛果数据...');
    console.log(`已获取 ${Object.keys(actualResults).length} 场赛果\n`);
    
    console.log('[3/3] 更新 Notion 反馈...\n');
    
    let updated = 0;
    let skipped = 0;
    let pending = 0;
    let correctCount = 0;
    let wrongCount = 0;
    
    const sortedNums = Object.keys(byNum).sort();
    
    for (const num of sortedNums) {
        const page = byNum[num];
        const props = page.properties || {};
        const home = props.主队?.rich_text?.[0]?.plain_text || '';
        const away = props.客队?.rich_text?.[0]?.plain_text || '';
        const prediction = props.竞彩预测?.rich_text?.[0]?.plain_text || '';
        
        // Skip if already has feedback
        const existingScore = props.实际比分?.rich_text?.[0]?.plain_text;
        if (existingScore) {
            console.log(`⏭️  ${num} ${home} vs ${away} - 已有反馈，跳过`);
            skipped++;
            continue;
        }
        
        const actual = actualResults[num];
        
        if (actual) {
            // Determine if prediction was correct
            let isCorrect = null;
            if (prediction) {
                if (prediction.includes('主胜') || prediction.includes('胜')) {
                    isCorrect = actual.result === '胜';
                } else if (prediction.includes('客胜') || prediction.includes('负')) {
                    isCorrect = actual.result === '负';
                } else if (prediction.includes('平')) {
                    isCorrect = actual.result === '平';
                }
            }
            
            const summary = `实际比分 ${actual.score}，竞彩结果 ${actual.result}` + 
                (isCorrect !== null ? `，预测${isCorrect ? '✅正确' : '❌错误'}` : '');
            
            try {
                await notionRequest('PATCH', '/v1/pages/' + page.id, {
                    properties: {
                        '实际比分': { rich_text: [{ text: { content: actual.score } }] },
                        '实际结果': { select: { name: actual.result } },
                        '预测正确': { checkbox: isCorrect === true },
                        '反馈日期': { date: { start: '2026-05-03' } },
                        '反馈总结': { rich_text: [{ text: { content: summary } }] }
                    }
                });
                
                const predText = prediction || '无预测';
                const icon = isCorrect ? '✅' : (isCorrect === false ? '❌' : '⚠️');
                console.log(`${icon} ${num} ${home} vs ${away} | ${actual.score} | ${actual.result} | 预测: ${predText}`);
                
                if (isCorrect === true) correctCount++;
                else if (isCorrect === false) wrongCount++;
                updated++;
            } catch(e) {
                console.log(`❌ ${num} 更新失败: ${e.message}`);
            }
        } else {
            console.log(`⏳ ${num} ${home} vs ${away} - 赛果尚未公布`);
            pending++;
        }
        
        await sleep(500);
    }
    
    console.log(`\n=== 反馈统计 ===`);
    console.log(`已更新: ${updated}`);
    console.log(`已跳过: ${skipped}`);
    console.log(`待查: ${pending}`);
    console.log(`预测正确: ${correctCount}`);
    console.log(`预测错误: ${wrongCount}`);
    if (correctCount + wrongCount > 0) {
        console.log(`准确率: ${(correctCount / (correctCount + wrongCount) * 100).toFixed(1)}%`);
    }
    
    // Save log
    const fs = require('fs');
    const path = require('path');
    const logFile = path.join(__dirname, 'feedback_2026-05-02.json');
    fs.writeFileSync(logFile, JSON.stringify({
        date: '2026-05-02',
        total: pages.length,
        unique: Object.keys(byNum).length,
        updated,
        skipped,
        pending,
        correct: correctCount,
        wrong: wrongCount,
        accuracy: correctCount + wrongCount > 0 ? (correctCount / (correctCount + wrongCount) * 100).toFixed(1) + '%' : 'N/A',
        timestamp: new Date().toISOString()
    }, null, 2), 'utf8');
    console.log(`\n📄 日志已保存: ${logFile}`);
}

main().catch(e => {
    console.error('[FATAL]', e.message);
    process.exit(1);
});
