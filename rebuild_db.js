// 删除旧数据库，重建完整Schema的新数据库
const https = require('https');

const API_KEY = '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';
const PARENT_ID = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71';

const DATABASE_ID = '93490bfb-ac43-49be-a24d-9e3e5a225991';

// 新Schema定义（反馈列放最后）
const SCHEMA = {
    '竞彩编号': { rich_text: {} },
    '比赛日期': { date: {} },
    '联赛': { rich_text: {} },
    '主队': { rich_text: {} },
    '客队': { rich_text: {} },
    '竞彩预测': { rich_text: {} },
    '竞彩信心': { select: { options: [
        { name: '强' },
        { name: '中' },
        { name: '弱' },
        { name: '回避' }
    ]}},
    '最终报告': { rich_text: {} },
    '盘路匹配': { rich_text: {} },
    '欧赔趋势': { rich_text: {} },
    '让球趋势': { rich_text: {} },
    '亚盘趋势': { rich_text: {} },
    '百家对比': { rich_text: {} },
    '实际比分': { rich_text: {} },
    '实际结果': { select: { options: [
        { name: '胜' },
        { name: '平' },
        { name: '负' }
    ]}},
    '预测正确': { checkbox: {} },
    '反馈日期': { date: {} },
    '反馈总结': { rich_text: {} },
    '备注': { rich_text: {} },
};

function archiveDatabase(id) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ archived: true });
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages/' + id,
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

function createDatabase() {
    return new Promise((resolve, reject) => {
        const pageData = {
            parent: { type: 'page_id', page_id: PARENT_ID },
            title: [{ text: { content: '竞彩比赛追踪' } }],
            properties: {
                'Name': { title: {} }
            },
            ...SCHEMA
        };
        const data = JSON.stringify(pageData);
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/databases',
            method: 'POST',
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
    console.log('📊 重建竞彩数据库（完整版Schema）\n');
    
    // 1. 删除旧数据库
    console.log('[1/2] 删除旧数据库...');
    await archiveDatabase(DATABASE_ID);
    console.log('✅ 旧数据库已删除\n');
    
    // 2. 创建新数据库
    console.log('[2/2] 创建新数据库...');
    const { status, data } = await createDatabase();
    if (status !== 200) {
        console.error('❌ 创建失败:', data.message);
        process.exit(1);
    }
    
    console.log('✅ 数据库创建成功！');
    console.log(`   ID: ${data.id}`);
    console.log(`   URL: ${data.url}`);
    console.log(`   属性数量: ${Object.keys(data.properties).length}`);
    console.log(`   属性: ${Object.keys(data.properties).join(', ')}`);
    
    // 3. 保存新配置
    const fs = require('fs');
    fs.writeFileSync('jingcai/config.js', `// 竞彩Notion配置（自动生成）\nmodule.exports = {\n  DATABASE_ID: '${data.id}'\n};\n`, 'utf8');
    console.log(`\n📄 配置已更新: jingcai/config.js`);
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
