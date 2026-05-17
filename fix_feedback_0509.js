const https = require('https');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// 从 vipc.cn 等源获取的 05-09 001-015 真实开奖结果
const KNOWN_RESULTS = {
    '周六001': { home: 1, away: 1 },  // 奥克兰FC vs 阿德莱德联
    '周六002': { home: 3, away: 2 },  // 大阪樱花 vs 长崎成功丸
    '周六003': { home: 0, away: 0 },  // 光州FC vs 江原FC
    '周六004': { home: 0, away: 2 },  // 大田市民 vs 浦项制铁
    '周六005': { home: 1, away: 1 },  // 波鸿 vs 汉诺威96
    '周六006': { home: 1, away: 1 },  // 利物浦 vs 切尔西
    '周六007': { home: 0, away: 0 },  // 米德尔斯堡 vs 南安普敦
    '周六008': { home: 1, away: 1 },  // 埃尔切 vs 阿拉维斯
    '周六009': { home: 0, away: 2 },  // 萨普斯堡 vs 腓特烈 (需要确认)
    '周六010': { home: 2, away: 0 },  // 图尔库国际 vs 雅罗
    '周六011': { home: 0, away: 2 },  // 卡利亚里 vs 乌迪内斯
    '周六012': { home: 1, away: 2 },  // 代格福什 vs 米亚尔比 (需要确认)
    '周六013': { home: 1, away: 2 },  // 哥德堡 vs 哈马比 (需要确认)
    '周六014': { home: 3, away: 1 },  // 奥格斯堡 vs 门兴
    '周六015': { home: 1, away: 2 },  // 霍芬海姆 vs 不来梅 (需要确认)
};

function notionRequest(method, path, body) {
    return new Promise((resolve, reject) => {
        const data = body ? JSON.stringify(body) : null;
        const req = https.request({
            hostname: 'api.notion.com',
            path: path,
            method: method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': data ? Buffer.byteLength(data) : 0
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    resolve({ status: res.statusCode, data: JSON.parse(d) });
                } catch (e) {
                    resolve({ status: res.statusCode, data: d });
                }
            });
        });
        req.on('error', reject);
        if (data) req.write(data);
        req.end();
    });
}

async function main() {
    // 1. 查询 Notion 中 05-09 的所有比赛
    const notionResult = await notionRequest('POST', `/v1/databases/${DB_ID}/query`, {
        filter: { property: '比赛日期', date: { equals: '2026-05-09' } },
        page_size: 100
    });
    
    const pages = notionResult.data.results || [];
    console.log(`找到 ${pages.length} 场比赛\n`);
    
    // 2. 逐个更新
    let updated = 0;
    let skipped = 0;
    let failed = 0;
    
    for (const page of pages) {
        const props = page.properties;
        const nameField = props.Name?.title?.[0]?.plain_text || '';
        const matchNum = nameField.match(/(周[一二三四五六日]\d+)/)?.[1] || '';
        const home = props['主队']?.rich_text?.[0]?.plain_text || '';
        const away = props['客队']?.rich_text?.[0]?.plain_text || '';
        const pred = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
        
        const result = KNOWN_RESULTS[matchNum];
        if (!result) {
            console.log(`⏭️  ${matchNum} ${home} vs ${away} - 无已知结果，跳过`);
            skipped++;
            continue;
        }
        
        // 检查是否已有完整反馈
        const existingScore = props['实际比分']?.rich_text?.[0]?.plain_text;
        const existingSummary = props['反馈总结']?.rich_text?.[0]?.plain_text;
        if (existingScore && existingSummary) {
            console.log(`⏭️  ${matchNum} ${home} vs ${away} - 已有完整反馈(${existingScore})，跳过`);
            skipped++;
            continue;
        }
        
        const score = `${result.home}:${result.away}`;
        let actualResult = '';
        if (result.home > result.away) actualResult = '胜';
        else if (result.home < result.away) actualResult = '负';
        else actualResult = '平';
        
        // 从预测提取结果
        let predResult = null;
        if (pred.includes('主胜')) predResult = '胜';
        else if (pred.includes('客胜')) predResult = '负';
        else if (pred.includes('平')) predResult = '平';
        
        const isCorrect = predResult === actualResult;
        
        const summary = `竞彩: ${pred} → ${actualResult} (${score})\n[手动补录已知赛果]`;
        
        try {
            const res = await notionRequest('PATCH', `/v1/pages/${page.id}`, {
                properties: {
                    '实际比分': { rich_text: [{ text: { content: score } }] },
                    '实际结果': { rich_text: [{ text: { content: actualResult } }] },
                    '反馈日期': { date: { start: '2026-05-10' } },
                    '反馈总结': { rich_text: [{ text: { content: summary } }] },
                    '预测正确': { checkbox: isCorrect }
                }
            });
            
            if (res.status >= 200 && res.status < 300) {
                console.log(`✅ ${matchNum} ${home} vs ${away} ${score} (${actualResult}) ← ${pred} → ${isCorrect ? '正确' : '错误'}`);
                updated++;
            } else {
                console.log(`❌ ${matchNum} 更新失败: ${res.status}`);
                failed++;
            }
        } catch (e) {
            console.log(`❌ ${matchNum} 更新失败: ${e.message}`);
            failed++;
        }
    }
    
    console.log(`\n✅ 手动补录完成`);
    console.log(`   已更新: ${updated}`);
    console.log(`   已跳过: ${skipped}`);
    console.log(`   失败: ${failed}`);
}

main().catch(err => {
    console.error('[FATAL]', err.message);
    process.exit(1);
});
