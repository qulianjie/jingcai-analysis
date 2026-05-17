// 调整竞彩数据库列 - 隐藏主场、客场、联赛、编号列
const https = require('https');
const fs = require('fs');
const API_KEY = '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';

// 先找到当前的竞彩数据库
const DB_ID = '79d2bdc1-3b01-40f8-8ab4-7a615b3fbee8';

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
                try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
                catch(e) { resolve({ status: res.statusCode, data: d }); }
            });
        });
        req.on('error', reject);
        if (body) req.write(body);
        req.end();
    });
}

// Notion API不能直接隐藏列，但可以通过调整视图来实现
// 先检查当前数据库状态
async function main() {
    console.log('📊 调整竞彩数据库列\n');
    
    // 检查数据库
    const { data: db } = await notionRequest('GET', `/v1/databases/${DB_ID}`);
    console.log('数据库:', db.title?.[0]?.plain_text);
    console.log('属性:', Object.keys(db.properties || {}).join(', '));
    console.log('属性数量:', Object.keys(db.properties || {}).length);
    
    // 获取data_source ID
    const dsId = db.data_sources?.[0]?.id;
    if (!dsId) {
        console.log('\n未找到data_source，无法调整列');
        return;
    }
    console.log('data_source:', dsId);
    
    // 查询视图
    const { data: views } = await notionRequest('POST', `/v1/data_sources/${dsId}/query`, {
        page_size: 10
    });
    console.log('\n当前页面数:', views.results?.length || 0);
    
    // 尝试通过更新视图来隐藏列
    // 需要找到视图ID
    // 由于API限制，我们直接删除不需要的属性
    console.log('\n尝试通过修改数据库Schema来隐藏列...');
    
    // 隐藏列的方法：在视图中设置visible: false
    // 但这需要先获取视图ID，通过页面内容块查找
    
    // 先查父页面
    const parentId = db.parent?.page_id;
    if (parentId) {
        const { data: blocks } = await notionRequest('GET', `/v1/blocks/${parentId}/children?page_size=50`);
        console.log('父页面子块数:', blocks.results?.length || 0);
        
        // 查找视图
        for (const block of (blocks.results || [])) {
            if (block.type === 'view') {
                console.log('视图:', block.id, block.view?.title || '');
            }
        }
    }
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
