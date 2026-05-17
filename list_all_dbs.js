const https = require('https');

const API_KEY = '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';

// 搜索所有数据库
function searchAll() {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            filter: { value: 'database', property: 'object' },
            page_size: 100
        });

        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/search',
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
            res.on('end', () => resolve(JSON.parse(d)));
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    console.log('🔍 搜索所有数据库...\n');
    
    const result = await searchAll();
    const items = result.results || [];
    
    console.log(`找到 ${items.length} 个数据库:\n`);
    
    items.forEach((item, index) => {
        const title = item.title?.[0]?.plain_text || '(untitled)';
        const props = item.properties ? Object.keys(item.properties) : [];
        const isArchived = item.archived || false;
        
        // 只显示竞彩相关的
        if (title.includes('竞彩') || title.includes('match') || title.includes('Match')) {
            console.log(`[${index + 1}] ${isArchived ? '🗑️' : '📊'} ${title}`);
            console.log(`    ID: ${item.id}`);
            console.log(`    Props: ${props.length > 0 ? props.join(', ') : '(empty)'}`);
            console.log(`    Archived: ${isArchived}`);
            console.log(`    URL: ${item.url}`);
            console.log('');
        }
    });
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
