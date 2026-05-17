// Add properties to the new jingcai database
const https = require('https');
const key = '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';
const dbId = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const properties = {
    '竞彩编号': { rich_text: {} },
    '比赛日期': { date: {} },
    '联赛': { rich_text: {} },
    '主队': { rich_text: {} },
    '客队': { rich_text: {} },
    '竞彩预测': { rich_text: {} },
    '竞彩信心': { select: { options: [{ name: '高' }, { name: '中' }, { name: '低' }] } },
    '最终报告': { rich_text: {} },
    '盘路匹配': { rich_text: {} },
    '欧赔趋势': { rich_text: {} },
    '让球趋势': { rich_text: {} },
    '亚盘趋势': { rich_text: {} },
    '百家对比': { rich_text: {} },
    '实际比分': { rich_text: {} },
    '实际结果': { select: { options: [{ name: '主胜' }, { name: '平局' }, { name: '客胜' }] } },
    '预测正确': { checkbox: {} },
    '反馈日期': { date: {} },
    '反馈总结': { rich_text: {} },
    '备注': { rich_text: {} }
};

const data = JSON.stringify({ properties });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + dbId,
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
        if (res.statusCode === 200) {
            const r = JSON.parse(d);
            console.log('OK: Properties added');
            console.log('Field count:', Object.keys(r.properties || {}).length);
            Object.keys(r.properties || {}).forEach(k => console.log('  - ' + k));
        } else {
            console.log('Body:', d.substring(0, 1000));
        }
    });
});
req.on('error', e => console.error('FAIL:', e.message));
req.write(data);
req.end();
