// 从Notion拉取实际比分
const https = require('https');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-818d-b7cc-d8a433d05229';

async function notionRequest(method, path, body) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const req = https.request({
            hostname: 'api.notion.com',
            path: path,
            method: method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let body = '';
            res.on('data', c => body += c);
            res.on('end', () => resolve({ status: res.statusCode, data: body }));
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    // 拉取所有记录
    let allResults = [];
    let cursor = null;
    
    do {
        const body = {
            page_size: 100
        };
        if (cursor) body.start_cursor = cursor;
        
        const res = await notionRequest('POST', '/v1/databases/' + DB_ID + '/query', body);
        const data = JSON.parse(res.data);
        allResults = allResults.concat(data.results || []);
        cursor = data.has_more ? data.next_cursor : null;
    } while (cursor);
    
    console.log(`找到 ${allResults.length} 条记录`);
    
    // 提取比分
    const scoreMap = {};
    for (const page of allResults) {
        const props = page.properties;
        const matchNum = props['竞彩编号']?.rich_text?.[0]?.plain_text || '';
        const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
        if (matchNum && score) {
            scoreMap[matchNum] = score;
        }
    }
    
    console.log(`有比分的: ${Object.keys(scoreMap).length}场`);
    
    // 输出
    for (const [k, v] of Object.entries(scoreMap).sort()) {
        console.log(`${k}: ${v}`);
    }
}

main().catch(console.error);
