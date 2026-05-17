const https = require('https');

const API_KEY = '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';

// 已知的竞彩数据库 ID
const KNOWN_DB_IDS = [
    '7ee379c2-f436-4ed9-ab5a-49ea9991634a',
    'e3026622-c86a-4671-9bd0-2aa316694d44',
    'c935350b-7dcc-44f9-9f79-8f341a22a470',
    '3bd07444-2c50-4be0-9463-7b0be9910230',
    '85f4ce8c-d1e9-4f0d-9e35-6eb23c0ab010'  // 最新创建的
];

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

function deleteDatabase(id, title) {
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/blocks/' + id,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                const result = JSON.parse(d);
                if (result.archived) {
                    console.log(`✅ 已删除: ${title}`);
                } else {
                    console.log(`⚠️ 状态异常: ${title}`);
                }
                resolve(result);
            });
        });
        req.on('error', reject);
        req.write(JSON.stringify({ archived: true }));
        req.end();
    });
}

async function main() {
    console.log('🔍 检查竞彩数据库状态...\n');
    
    const emptyDbs = [];
    
    for (const id of KNOWN_DB_IDS) {
        const { status, data } = await getDatabase(id);
        
        if (status === 200) {
            const title = data.title?.[0]?.plain_text || '(untitled)';
            const props = data.properties ? Object.keys(data.properties) : [];
            const isEmpty = props.length === 0;
            const isArchived = data.archived || false;
            
            console.log(`${isEmpty ? '❌' : '✅'} ${title}`);
            console.log(`   ID: ${id}`);
            console.log(`   Properties: ${props.length > 0 ? props.join(', ') : '(empty)'}`);
            console.log(`   Archived: ${isArchived}`);
            console.log(`   URL: ${data.url}`);
            console.log('');
            
            if (isEmpty || isArchived) {
                emptyDbs.push({ id, title });
            }
        } else {
            console.log(`⚠️ ${id} - Status: ${status}`);
            console.log(`   ${data.message || 'Unknown error'}`);
            console.log('');
        }
    }
    
    if (emptyDbs.length > 0) {
        console.log(`\n🗑️ 找到 ${emptyDbs.length} 个空/已归档数据库，准备删除...\n`);
        
        for (const db of emptyDbs) {
            await deleteDatabase(db.id, db.title);
        }
        
        console.log('\n✅ 清理完成');
    } else {
        console.log('\n✅ 所有数据库都有数据且未归档');
    }
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
