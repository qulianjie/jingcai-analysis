// 清理新数据库中的重复条目
const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function notionRequest(method, endpoint, data) {
    return new Promise((resolve, reject) => {
        const body = data ? JSON.stringify(data) : null;
        const req = https.request({
            hostname: 'api.notion.com',
            path: endpoint,
            method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
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

async function main() {
    console.log('📊 清理新数据库重复条目\n');
    
    // 获取所有条目
    const { data } = await notionRequest('POST', `/v1/databases/${DB_ID}/query`, { page_size: 200 });
    const pages = data.results || [];
    console.log('共', pages.length, '条\n');
    
    // 按"比赛"列分组
    const byMatch = {};
    pages.forEach(p => {
        const match = p.properties['比赛']?.rich_text?.[0]?.plain_text || '';
        if (!match) return;
        if (!byMatch[match]) byMatch[match] = [];
        byMatch[match].push(p);
    });
    
    let toDelete = [];
    let kept = [];
    for (const [match, group] of Object.entries(byMatch)) {
        if (group.length <= 1) {
            kept.push(match);
            continue;
        }
        kept.push(match);
        // 保留第一条，删除其他
        for (let i = 1; i < group.length; i++) {
            toDelete.push({ id: group[i].id, match });
        }
    }
    
    console.log('保留:', kept.length, '条');
    console.log('待删除:', toDelete.length, '条\n');
    
    if (toDelete.length === 0) {
        console.log('没有重复');
        return;
    }
    
    let deleted = 0;
    for (const item of toDelete) {
        const result = await notionRequest('PATCH', `/v1/pages/${item.id}`, { archived: true });
        if (result.status === 200) {
            deleted++;
            console.log('已删除:', item.match.substring(0, 40));
        }
        await new Promise(r => setTimeout(r, 200));
    }
    
    console.log(`\n完成！删除了 ${deleted}/${toDelete.length} 条重复`);
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
