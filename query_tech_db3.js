// 先查父页面找到技术学习日报数据库
const https = require('https');
const API_KEY = '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';

const PARENT_PAGE = '35391ad7-17ba-80ae-9770-eb5d366fb56b';

function notionGet(path) {
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: path,
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
                catch(e) { resolve({ status: res.statusCode, data: d }); }
            });
        });
        req.on('error', reject);
        req.end();
    });
}

async function main() {
    // 1. 获取父页面内容块，找数据库
    console.log('[1] 获取父页面子块...');
    let { data } = await notionGet(`/v1/blocks/${PARENT_PAGE}/children?page_size=100`);
    console.log('Status:', data.object);
    console.log('Results:', data.results?.length || 0);
    
    // 找数据库块
    const dbBlocks = (data.results || []).filter(b => b.type === 'child_database');
    console.log(`\n找到 ${dbBlocks.length} 个子数据库\n`);
    
    for (const db of dbBlocks) {
        console.log(`Database: ${db.id} (${db.type})`);
        console.log(`  Title: ${db.child_database?.title || 'N/A'}`);
    }
    
    // 2. 尝试直接查 dc3cfd28 是不是页面ID
    console.log('\n[2] 检查 dc3cfd28 是否为页面...');
    const pageResult = await notionGet(`/v1/pages/dc3cfd289c6c49dd93d28fb2534f5284`);
    if (pageResult.status === 200) {
        console.log('  是页面！Title:', pageResult.data.properties?.Name?.title?.[0]?.plain_text || 'N/A');
    } else {
        console.log('  不是页面');
    }
    
    // 3. 尝试查 dc3cfd28 是否为数据库
    console.log('\n[3] 检查 dc3cfd28 是否为数据库...');
    const dbResult = await notionGet(`/v1/databases/dc3cfd289c6c49dd93d28fb2534f5284`);
    if (dbResult.status === 200) {
        console.log('  是数据库！Title:', dbResult.data.title?.[0]?.plain_text);
        console.log('  is_inline:', dbResult.data.is_inline);
        console.log('  properties:', JSON.stringify(dbResult.data.properties, null, 2));
    } else {
        console.log('  不是数据库:', dbResult.data?.message || dbResult.status);
    }
}

main().catch(err => console.error(err));
