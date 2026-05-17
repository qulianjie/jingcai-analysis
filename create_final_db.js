// 创建带完整Schema的竞彩数据库
const https = require('https');

const API_KEY = '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';
const PARENT_ID = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71';

function notionRequest(method, endpoint, data) {
    return new Promise((resolve, reject) => {
        const body = data ? JSON.stringify(data) : null;
        const req = https.request({
            hostname: 'api.notion.com',
            path: endpoint,
            method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body || ''),
            },
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
        if (body) req.write(body);
        req.end();
    });
}

async function main() {
    console.log('📊 创建竞彩数据库（完整版Schema）\n');
    
    // 创建数据库 - properties必须在创建时传入
    const props = {
        'Name': { title: {} },
        '竞彩编号': { rich_text: {} },
        '比赛日期': { date: {} },
        '联赛': { rich_text: {} },
        '主队': { rich_text: {} },
        '客队': { rich_text: {} },
        '竞彩预测': { rich_text: {} },
        '竞彩信心': { select: { options: [
            { name: '强' }, { name: '中' }, { name: '弱' }, { name: '回避' }
        ]}},
        '最终报告': { rich_text: {} },
        '盘路匹配': { rich_text: {} },
        '欧赔趋势': { rich_text: {} },
        '让球趋势': { rich_text: {} },
        '亚盘趋势': { rich_text: {} },
        '百家对比': { rich_text: {} },
        '实际比分': { rich_text: {} },
        '实际结果': { select: { options: [
            { name: '胜' }, { name: '平' }, { name: '负' }
        ]}},
        '预测正确': { checkbox: {} },
        '反馈日期': { date: {} },
        '反馈总结': { rich_text: {} },
        '备注': { rich_text: {} },
    };
    
    console.log('创建数据库...');
    const { status, data: db } = await notionRequest('POST', '/v1/databases', {
        parent: { type: 'page_id', page_id: PARENT_ID },
        title: [{ text: { content: '竞彩比赛追踪' } }],
        properties: props
    });
    
    if (status !== 200) {
        console.error('❌ 创建失败:', db.message || JSON.stringify(db).substring(0, 500));
        process.exit(1);
    }
    
    console.log('✅ 数据库创建成功！');
    console.log(`   ID: ${db.id}`);
    console.log(`   URL: ${db.url}`);
    console.log(`   属性数量: ${Object.keys(db.properties).length}`);
    console.log(`   属性: ${Object.keys(db.properties).join(', ')}`);
    
    // 更新sync_notion.js
    const fs = require('fs');
    const syncPath = 'jingcai/sync_notion.js';
    let syncContent = fs.readFileSync(syncPath, 'utf8');
    syncContent = syncContent.replace(
        /const DATABASE_ID = '[^']+';/,
        `const DATABASE_ID = '${db.id}';`
    );
    fs.writeFileSync(syncPath, syncContent, 'utf8');
    console.log(`\n✅ 同步脚本已更新: jingcai/sync_notion.js`);
    
    console.log('\n✅ 全部完成！');
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
