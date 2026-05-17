const https = require('https');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// 查询 5月10日 的所有比赛
function queryMatches() {
    const data = JSON.stringify({
        filter: { and: [{ property: '比赛日期', date: { equals: '2026-05-10' } }] },
        page_size: 100
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${DB_ID}/query`,
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
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

// 清除一场比赛的比分
function clearScore(pageId, matchNum) {
    const data = JSON.stringify({
        properties: {
            '实际比分': { rich_text: [] },
            '实际结果': { rich_text: [] },
            '反馈日期': { date: null },
            '反馈总结': { rich_text: [] },
            '预测正确': { checkbox: false },
            '让球预测正确': { checkbox: false }
        }
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/pages/${pageId}`,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(d));
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    console.log('清除 5月10日 错误比分...\n');
    
    const result = await queryMatches();
    const pages = result.results || [];
    
    let cleared = 0;
    for (const page of pages) {
        const name = page.properties.Name?.title?.[0]?.plain_text || '';
        const score = page.properties['实际比分']?.rich_text?.[0]?.plain_text;
        
        if (score) {
            // 检查是否是错误比分（时间格式如 22:45, 4:30, 0:30 等）
            const parts = score.split(':');
            if (parts.length === 2) {
                const a = parseInt(parts[0]);
                const b = parseInt(parts[1]);
                // 时间格式：第二部分 >= 30 或 第一部分 > 15
                const isWrong = b >= 30 || a > 15;
                
                if (isWrong) {
                    console.log(`清除: ${name} - 错误比分: ${score}`);
                    await clearScore(page.id, name);
                    cleared++;
                }
            }
        }
    }
    
    console.log(`\n✅ 已清除 ${cleared} 场错误比分`);
}

main().catch(err => console.error(err));
