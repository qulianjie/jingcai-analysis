// 创建Notion match数据库的23个新字段
// 用法: node jingcai/create_odds_fields.js
const https = require('https');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const headers = {
    'Authorization': 'Bearer ' + API_KEY,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
};

// 需要创建的字段列表
const fields = [
    // 终盘数据（feedback.js从sporttery.cn实时获取）
    { name: '终盘竞彩欧赔胜', type: 'number', format: 'number' },
    { name: '终盘竞彩欧赔平', type: 'number', format: 'number' },
    { name: '终盘竞彩欧赔负', type: 'number', format: 'number' },
    { name: '终盘百家欧赔胜', type: 'number', format: 'number' },
    { name: '终盘百家欧赔平', type: 'number', format: 'number' },
    { name: '终盘百家欧赔负', type: 'number', format: 'number' },
    { name: '终盘Interwetten胜', type: 'number', format: 'number' },
    { name: '终盘Interwetten平', type: 'number', format: 'number' },
    { name: '终盘Interwetten负', type: 'number', format: 'number' },
    { name: '终盘让球指数胜', type: 'number', format: 'number' },
    { name: '终盘让球指数平', type: 'number', format: 'number' },
    { name: '终盘让球指数负', type: 'number', format: 'number' },
    { name: '终盘澳门亚盘', type: 'rich_text' },
    // 非终盘数据（sync_notion.js从本地报告提取）
    { name: '百家欧赔胜', type: 'number', format: 'number' },
    { name: '百家欧赔平', type: 'number', format: 'number' },
    { name: '百家欧赔负', type: 'number', format: 'number' },
    { name: 'Interwetten胜', type: 'number', format: 'number' },
    { name: 'Interwetten平', type: 'number', format: 'number' },
    { name: 'Interwetten负', type: 'number', format: 'number' },
    { name: '让球指数胜', type: 'number', format: 'number' },
    { name: '让球指数平', type: 'number', format: 'number' },
    { name: '让球指数负', type: 'number', format: 'number' },
    { name: '澳门亚盘', type: 'rich_text' },
];

function notionRequest(method, endpoint, data) {
    return new Promise((resolve, reject) => {
        const body = data ? JSON.stringify(data) : null;
        const req = https.request({
            hostname: 'api.notion.com',
            path: endpoint,
            method,
            headers: {
                ...headers,
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

async function createField(propName, propConfig) {
    const endpoint = `/v1/databases/${DB_ID}`;
    const data = { properties: {} };
    data.properties[propName] = propConfig;

    const res = await notionRequest('PATCH', endpoint, data);
    if (res.status === 200) {
        console.log(`  ✅ ${propName}`);
        return true;
    } else {
        console.log(`  ❌ ${propName}: ${JSON.stringify(res.data).substring(0, 200)}`);
        return false;
    }
}

async function main() {
    console.log('Creating 23 new odds fields in Notion match database...\n');
    
    let created = 0;
    let failed = 0;
    
    for (const field of fields) {
        let propConfig;
        if (field.type === 'number') {
            propConfig = { number: { format: field.format || 'number' } };
        } else {
            propConfig = { rich_text: {} };
        }
        
        const ok = await createField(field.name, propConfig);
        if (ok) created++;
        else failed++;
    }
    
    console.log(`\nDone: ${created} created, ${failed} failed`);
}

main().catch(e => {
    console.error('Error:', e.message);
    process.exit(1);
});
