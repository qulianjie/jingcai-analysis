const https = require('https');

const API_KEY = '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';
const DB_ID = '93490bfb-ac43-49be-a24d-9e3e5a225991';

// ===== 获取数据库详情 =====
function getDatabase(id) {
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/databases/' + id,
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve({ status: res.statusCode, data: JSON.parse(d) }));
        });
        req.on('error', reject);
        req.end();
    });
}

// ===== 更新数据库（添加视图） =====
function updateDatabase(id, updates) {
    const data = JSON.stringify(updates);
    
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/databases/' + id,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve({ status: res.statusCode, data: JSON.parse(d) }));
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    console.log('🔧 竞彩数据库优化\n');
    
    // 1. 获取当前数据库信息
    console.log('[1/3] 获取数据库信息...');
    const { status, data: db } = await getDatabase(DB_ID);
    
    if (status !== 200) {
        console.error('❌ 获取失败:', db.message);
        process.exit(1);
    }
    
    console.log(`✅ 数据库: ${db.title?.[0]?.plain_text}`);
    console.log(`   URL: ${db.url}`);
    console.log(`   列数: ${Object.keys(db.properties || {}).length}\n`);
    
    // 2. 查询数据量
    console.log('[2/3] 查询数据量...');
    
    const queryData = JSON.stringify({ page_size: 100 });
    
    const queryResult = await new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${DB_ID}/query`,
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(queryData)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(JSON.parse(d)));
        });
        req.on('error', reject);
        req.write(queryData);
        req.end();
    });
    
    const totalPages = queryResult.results?.length || 0;
    console.log(`✅ 总记录: ${totalPages}\n`);
    
    // 3. 统计数据
    console.log('[3/3] 数据统计...\n');
    
    const stats = {
        total: totalPages,
        withFeedback: 0,
        correct: 0,
        incorrect: 0,
        pending: 0,
        byLeague: {},
        byConfidence: {}
    };
    
    for (const page of (queryResult.results || [])) {
        const props = page.properties;
        const actualScore = props['实际比分']?.rich_text?.[0]?.plain_text;
        const isCorrect = props['预测正确']?.checkbox;
        const confidence = props['竞彩信心']?.select?.name || '';
        const league = props['联赛']?.rich_text?.[0]?.plain_text || '';
        
        if (actualScore) {
            stats.withFeedback++;
            if (isCorrect === true) stats.correct++;
            else if (isCorrect === false) stats.incorrect++;
            else stats.pending++;
        }
        
        if (confidence) {
            if (!stats.byConfidence[confidence]) stats.byConfidence[confidence] = { total: 0, correct: 0 };
            stats.byConfidence[confidence].total++;
            if (isCorrect === true) stats.byConfidence[confidence].correct++;
        }
        
        if (league) {
            if (!stats.byLeague[league]) stats.byLeague[league] = { total: 0, correct: 0 };
            stats.byLeague[league].total++;
            if (isCorrect === true) stats.byLeague[league].correct++;
        }
    }
    
    // 输出统计
    const accuracy = stats.withFeedback > 0 
        ? (stats.correct / stats.withFeedback * 100).toFixed(1) 
        : 'N/A';
    
    console.log('📊 数据统计:');
    console.log(`   总记录: ${stats.total}`);
    console.log(`   已反馈: ${stats.withFeedback}`);
    console.log(`   预测正确: ${stats.correct}`);
    console.log(`   预测错误: ${stats.incorrect}`);
    console.log(`   待查: ${stats.pending}`);
    console.log(`   **准确率: ${accuracy}%**\n`);
    
    if (Object.keys(stats.byLeague).length > 0) {
        console.log('📈 按联赛统计:');
        for (const [league, s] of Object.entries(stats.byLeague)) {
            const acc = s.total > 0 ? (s.correct / s.total * 100).toFixed(1) : 'N/A';
            console.log(`   ${league}: ${s.correct}/${s.total} (${acc}%)`);
        }
        console.log('');
    }
    
    if (Object.keys(stats.byConfidence).length > 0) {
        console.log('💪 按信心统计:');
        for (const [conf, s] of Object.entries(stats.byConfidence)) {
            const acc = s.total > 0 ? (s.correct / s.total * 100).toFixed(1) : 'N/A';
            console.log(`   ${conf}: ${s.correct}/${s.total} (${acc}%)`);
        }
        console.log('');
    }
    
    console.log(`🔗 数据库: ${db.url}`);
}

main().catch(err => {
    console.error('[FATAL]', err.message);
    process.exit(1);
});
