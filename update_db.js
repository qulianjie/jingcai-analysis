const https = require('https');
const key = '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';
const dbId = 'e3026622-c86a-4671-9bd0-2aa316694d44';

const data = JSON.stringify({
  properties: {
    '竞彩编号': { rich_text: {} },
    '比赛日期': { date: {} },
    '联赛': { rich_text: {} },
    '主队': { rich_text: {} },
    '客队': { rich_text: {} },
    '竞彩预测': { select: { options: [{ name: '胜' }, { name: '平' }, { name: '负' }] } },
    '竞彩信心': { rich_text: {} },
    '最终报告': { url: {} },
    '实际比分': { rich_text: {} },
    '实际结果': { select: { options: [{ name: '胜' }, { name: '平' }, { name: '负' }] } },
    '预测正确': { checkbox: {} },
    '反馈日期': { date: {} },
    '反馈总结': { rich_text: {} },
    '盘路匹配': { rich_text: {} },
    '欧赔趋势': { rich_text: {} },
    '让球趋势': { rich_text: {} },
    '亚盘趋势': { rich_text: {} },
    '百家对比': { rich_text: {} },
    '备注': { rich_text: {} }
  }
});

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
    console.log('Response:', d);
    const j = JSON.parse(d);
    console.log('Status:', res.statusCode);
    console.log('Props:', Object.keys(j.properties || {}).join(', '));
  });
});

req.write(data);
req.end();
