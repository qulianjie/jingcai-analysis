const https = require('https');

const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

// 读取5月10日分组统计数据
const fs = require('fs');
const logData = JSON.parse(fs.readFileSync('C:/Users/lianjie/.openclaw/workspace/data/jingcai/feedback_2026-05-10.json', 'utf8'));

const groups = logData.groups;
const sortedGroups = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);

// Build table content
let content = `## 📊 2026-05-10分组统计（按竞彩/庄家/让球分组）\n\n`;
content += `| 竞彩 | 庄家 | 让球 | 场数 | 实际胜 | 实际平 | 实际负 |\n`;
content += `|------|------|------|------|--------|--------|--------|\n`;

for (const [key, stats] of sortedGroups) {
    const [pred, zj, rq] = key.split('|');
    content += `| ${pred} | ${zj} | ${rq} | ${stats.total} | ${stats.胜} | ${stats.平} | ${stats.负} |\n`;
}

let totalWins = 0, totalDraws = 0, totalLosses = 0;
for (const stats of Object.values(groups)) {
    totalWins += stats.胜;
    totalDraws += stats.平;
    totalLosses += stats.负;
}
const total = totalWins + totalDraws + totalLosses;
content += `\n**${total}场合计：胜${totalWins} 平${totalDraws} 负${totalLosses}**\n`;

const maxGroup = sortedGroups[0];
if (maxGroup) {
    const [key, stats] = maxGroup;
    const [pred, zj, rq] = key.split('|');
    content += `\n最大分组是「竞彩${pred} | 庄家${zj} | 让球${rq}」${stats.total}场，实际结果是胜${stats.胜}平${stats.平}负${stats.负}。\n`;
}

// Create page in the database
const data = JSON.stringify({
    parent: { database_id: DB_ID },
    properties: {
        '日期': {
            title: [{ text: { content: '2026-05-10' } }]
        }
    },
    children: [
        {
            object: 'block',
            type: 'paragraph',
            paragraph: {
                rich_text: [{ text: { content: content } }]
            }
        }
    ]
});

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/pages',
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
    res.on('end', () => {
        try {
            const r = JSON.parse(d);
            if (r.id) {
                console.log('✅ 已创建页面:', r.id);
                console.log('URL: https://notion.so/' + r.id.replace(/-/g, ''));
            } else {
                console.log('❌ 创建失败:', d);
            }
        } catch (e) {
            console.log('Parse error:', d);
        }
    });
});
req.on('error', e => console.log('Error:', e.message));
req.write(data);
req.end();
