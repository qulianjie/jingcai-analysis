// 调试：查看Notion API返回的完整响应
const https = require('https');
const fs = require('fs');

const API_KEY = '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';
const PARENT_ID = '35391ad7-17ba-804d-8e5b-ec1b55fe2f71';

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

async function main() {
    // 创建测试数据库
    const payload = {
        "parent": { "type": "page_id", "page_id": PARENT_ID },
        "title": [
            {
                "type": "text",
                "text": { "content": "竞彩比赛追踪-测试" }
            }
        ],
        "properties": {
            "Name": { "title": {} },
            "竞彩编号": { "rich_text": {} },
            "比赛日期": { "date": {} },
            "联赛": { "rich_text": {} },
            "主队": { "rich_text": {} },
            "客队": { "rich_text": {} },
            "竞彩预测": { "rich_text": {} },
            "竞彩信心": {
                "select": {
                    "options": [
                        { "name": "强", "color": "green" },
                        { "name": "中", "color": "yellow" },
                        { "name": "弱", "color": "orange" },
                        { "name": "回避", "color": "red" }
                    ]
                }
            },
            "最终报告": { "rich_text": {} },
            "盘路匹配": { "rich_text": {} },
            "欧赔趋势": { "rich_text": {} },
            "让球趋势": { "rich_text": {} },
            "亚盘趋势": { "rich_text": {} },
            "百家对比": { "rich_text": {} },
            "实际比分": { "rich_text": {} },
            "实际结果": {
                "select": {
                    "options": [
                        { "name": "胜", "color": "green" },
                        { "name": "平", "color": "yellow" },
                        { "name": "负", "color": "red" }
                    ]
                }
            },
            "预测正确": { "checkbox": {} },
            "反馈日期": { "date": {} },
            "反馈总结": { "rich_text": {} },
            "备注": { "rich_text": {} }
        }
    };
    
    console.log('发送请求...');
    console.log('Payload:', JSON.stringify(payload, null, 2).substring(0, 500));
    console.log('---');
    
    const result = await notionRequest('POST', '/v1/databases', payload);
    
    console.log('Status:', result.status);
    console.log('Full response:');
    console.log(JSON.stringify(result.data, null, 2));
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
