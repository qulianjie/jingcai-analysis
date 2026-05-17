const https = require('https');

const API_KEY = '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';
const PARENT_ID = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71';

// 新架构：比赛信息合并为一列，反馈列放最后
const COLUMNS = {
    '比赛': { rich_text: {} },           // 周X0XX 联赛 主队vs客队
    '竞彩编号': { rich_text: {} },
    '联赛': { rich_text: {} },
    '主队': { rich_text: {} },
    '客队': { rich_text: {} },
    '竞彩预测': { rich_text: {} },
    '让球预测': { rich_text: {} },
    '竞彩信心': { select: { options: [
        { name: '强' },
        { name: '中' },
        { name: '弱' },
        { name: '回避' }
    ]}},
    '盘路匹配': { rich_text: {} },
    '欧赔趋势': { rich_text: {} },
    '让球趋势': { rich_text: {} },
    '亚盘趋势': { rich_text: {} },
    '百家对比': { rich_text: {} },
    '综合分值': { rich_text: {} },
    '数据质量': { rich_text: {} },
    '实际比分': { rich_text: {} },
    '实际结果': { select: { options: [
        { name: '胜' },
        { name: '平' },
        { name: '负' }
    ]}},
    '让球结果': { select: { options: [
        { name: '让胜' },
        { name: '让平' },
        { name: '让负' }
    ]}},
    '预测正确': { checkbox: {} },
    '让球预测正确': { checkbox: {} },
    '反馈日期': { date: {} },
    '反馈总结': { rich_text: {} },
    '备注': { rich_text: {} }
};

function createDatabase() {
    return new Promise((resolve, reject) => {
        const pageData = {
            parent: { type: 'page_id', page_id: PARENT_ID },
            title: [{ text: { content: '竞彩比赛追踪' } }],
            properties: {
                'Name': { title: {} }
            }
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

function addProperty(dataSourceId, propName, config) {
    return new Promise((resolve, reject) => {
        const patchData = { properties: {} };
        patchData.properties[propName] = config;
        const data = JSON.stringify(patchData);
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/data_sources/' + dataSourceId,
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
            res.on('end', () => {
                try {
                    const result = JSON.parse(d);
                    if (res.statusCode === 200) {
                        console.log(`  ✅ ${propName}`);
                    } else {
                        console.log(`  ⚠️ ${propName}: ${res.statusCode} ${d.substring(0, 100)}`);
                    }
                    resolve({ status: res.statusCode, data: result });
                } catch (e) {
                    console.log(`  ⚠️ ${propName}: parse error`);
                    resolve({ status: res.statusCode });
                }
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

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

async function main() {
    console.log('📊 创建竞彩数据库 V2（新版字段结构）\n');
    
    // 1. 创建数据库
    console.log('[1/3] 创建数据库...');
    const { status, data: dbData } = await createDatabase();
    if (status !== 200) {
        console.error('❌ 创建失败:', dbData.message);
        process.exit(1);
    }
    const dbId = dbData.id;
    console.log(`✅ 数据库创建成功`);
    console.log(`   ID: ${dbId}`);
    console.log(`   URL: ${dbData.url}\n`);
    
    // 2. 获取 data_source ID
    console.log('[2/3] 获取 data_source ID...');
    const { data: dbInfo } = await getDatabase(dbId);
    const dataSourceId = dbInfo.data_sources?.[0]?.id;
    if (!dataSourceId) {
        console.error('❌ 无法获取 data_source ID');
        process.exit(1);
    }
    console.log(`✅ Data Source ID: ${dataSourceId}\n`);
    
    // 3. 添加列
    console.log('[3/3] 添加列...');
    const columnNames = Object.keys(COLUMNS);
    for (const colName of columnNames) {
        await addProperty(dataSourceId, colName, COLUMNS[colName]);
    }
    
    console.log('\n✅ 竞彩数据库 V2 创建完成！');
    console.log(`   数据库 ID: ${dbId}`);
    console.log(`   Data Source ID: ${dataSourceId}`);
    console.log(`   URL: ${dbData.url}`);
    
    // 输出到文件供后续使用
    const fs = require('fs');
    fs.writeFileSync('config_v2.json', JSON.stringify({ dbId, dataSourceId }, null, 2), 'utf8');
    console.log(`\n📄 配置已保存: jingcai/config_v2.json`);
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
