// 完整重建竞彩数据库
const https = require('https');
const fs = require('fs');

const API_KEY = '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';
const PARENT_ID = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71';
const OLD_DB_ID = '2bab3382-0d4f-4768-b215-eace04248e5e';

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
    console.log('📊 完整重建竞彩数据库\n');
    
    // 1. 删除旧数据库
    console.log('[1/3] 删除旧数据库...');
    const delResult = await notionRequest('PATCH', `/v1/pages/${OLD_DB_ID}`, { archived: true });
    console.log('✅ 旧数据库已删除\n');
    
    // 2. 创建新数据库
    console.log('[2/3] 创建新数据库...');
    const newDbPayload = {
        "parent": { "type": "page_id", "page_id": PARENT_ID },
        "title": [
            {
                "type": "text",
                "text": { "content": "竞彩比赛追踪" }
            }
        ],
        "properties": {
            "Name": { "title": {} },
            "竞彩编号": { "rich_text": {} },
            "比赛日期": { "date": {} },
            "联赛": { "rich_text": {} },
            "主队": { "rich_text": {} },
            "客队": { "rich_text": {} },
            "竞彩预测": { "rich_text": {} },
            "竞彩信心": {
                "select": {
                    "options": [
                        { "name": "强", "color": "green" },
                        { "name": "中", "color": "yellow" },
                        { "name": "弱", "color": "orange" },
                        { "name": "回避", "color": "red" }
                    ]
                }
            },
            "最终报告": { "rich_text": {} },
            "盘路匹配": { "rich_text": {} },
            "欧赔趋势": { "rich_text": {} },
            "让球趋势": { "rich_text": {} },
            "亚盘趋势": { "rich_text": {} },
            "百家对比": { "rich_text": {} },
            "实际比分": { "rich_text": {} },
            "实际结果": {
                "select": {
                    "options": [
                        { "name": "胜", "color": "green" },
                        { "name": "平", "color": "yellow" },
                        { "name": "负", "color": "red" }
                    ]
                }
            },
            "预测正确": { "checkbox": {} },
            "反馈日期": { "date": {} },
            "反馈总结": { "rich_text": {} },
            "备注": { "rich_text": {} }
        }
    };
    
    const createResult = await notionRequest('POST', '/v1/databases', newDbPayload);
    
    console.log('Response status:', createResult.status);
    
    if (createResult.status !== 200) {
        console.error('❌ 创建失败:', JSON.stringify(createResult.data).substring(0, 500));
        process.exit(1);
    }
    
    const newDb = createResult.data;
    const newDbId = newDb.id;
    const propsCount = newDb.properties ? Object.keys(newDb.properties).length : 0;
    
    console.log(`✅ 数据库创建成功！`);
    console.log(`   ID: ${newDbId}`);
    console.log(`   URL: ${newDb.url}`);
    console.log(`   属性数量: ${propsCount}`);
    
    // 3. 更新sync_notion.js
    console.log('\n[3/3] 更新同步脚本...');
    const syncPath = 'jingcai/sync_notion.js';
    let syncContent = fs.readFileSync(syncPath, 'utf8');
    syncContent = syncContent.replace(
        /const DATABASE_ID = '[^']+';/,
        `const DATABASE_ID = '${newDbId}';`
    );
    fs.writeFileSync(syncPath, syncContent, 'utf8');
    console.log('✅ 同步脚本已更新\n');
    
    console.log('✅ 全部完成！可以重新运行同步了');
}

main().catch(err => {
    console.error('Error:', err.message);
    console.error(err.stack);
    process.exit(1);
});
