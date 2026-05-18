const https = require('https');
const key = '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';
const dbId = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function patch(path, body) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const req = https.request({
            hostname: 'api.notion.com',
            path: path,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + key,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                console.log('Status:', res.statusCode);
                try {
                    const r = JSON.parse(d);
                    if (r.properties) {
                        console.log('Properties:', Object.keys(r.properties).length);
                        Object.keys(r.properties).forEach(k => console.log('  -', k));
                    } else {
                        console.log('Response:', d.substring(0, 500));
                    }
                    resolve(r);
                } catch(e) {
                    console.log('Raw:', d.substring(0, 500));
                    resolve(d);
                }
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    // Try adding properties one by one
    const props = [
        { name: '竞彩编号', config: { rich_text: {} } },
        { name: '比赛日期', config: { date: {} } },
        { name: '联赛', config: { rich_text: {} } },
        { name: '主队', config: { rich_text: {} } },
        { name: '客队', config: { rich_text: {} } },
        { name: '竞彩预测', config: { rich_text: {} } },
        { name: '竞彩信心', config: { select: { options: [{ name: '高' }, { name: '中' }, { name: '低' }] } } },
        { name: '最终报告', config: { rich_text: {} } },
        { name: '盘路匹配', config: { rich_text: {} } },
        { name: '欧赔趋势', config: { rich_text: {} } },
        { name: '让球趋势', config: { rich_text: {} } },
        { name: '亚盘趋势', config: { rich_text: {} } },
        { name: '百家对比', config: { rich_text: {} } },
        { name: '实际比分', config: { rich_text: {} } },
        { name: '实际结果', config: { select: { options: [{ name: '主胜' }, { name: '平局' }, { name: '客胜' }] } } },
        { name: '预测正确', config: { checkbox: {} } },
        { name: '反馈日期', config: { date: {} } },
        { name: '反馈总结', config: { rich_text: {} } },
        { name: '备注', config: { rich_text: {} } }
    ];
    
    // Try all at once first
    const properties = {};
    props.forEach(p => {
        properties[p.name] = p.config;
    });
    
    console.log('Adding all properties at once...');
    await patch('/v1/databases/' + dbId, { properties });
    
    // Verify
    console.log('\nVerifying...');
    const https = require('https');
    const req = https.request({
        hostname: 'api.notion.com',
        path: '/v1/databases/' + dbId,
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + key,
            'Notion-Version': '2025-09-03'
        }
    }, res => {
        let d = '';
        res.on('data', c => d += c);
        res.on('end', () => {
            const r = JSON.parse(d);
            console.log('After PATCH - Properties count:', Object.keys(r.properties || {}).length);
            Object.keys(r.properties || {}).forEach(k => console.log('  -', k));
        });
    });
    req.end();
}

main().catch(console.error);
