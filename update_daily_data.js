const https = require('https');
const fs = require('fs');

const API_KEY = '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';

// 读取5月10日数据
const logData = JSON.parse(fs.readFileSync('C:/Users/lianjie/.openclaw/workspace/data/jingcai/feedback_2026-05-10.json', 'utf8'));
const groups = logData.groups;
const sortedGroups = Object.entries(groups).sort((a, b) => b[1].total - a[1].total);

// 计算总计
let totalWins = 0, totalDraws = 0, totalLosses = 0;
for (const stats of Object.values(groups)) {
    totalWins += stats.胜;
    totalDraws += stats.平;
    totalLosses += stats.负;
}
const total = totalWins + totalDraws + totalLosses;

// 最大分组
const maxGroup = sortedGroups[0];
const [maxKey, maxStats] = maxGroup;
const [pred, zj, rq] = maxKey.split('|');

// 分组明细
let detail = '';
for (const [key, stats] of sortedGroups) {
    const [p, z, r] = key.split('|');
    detail += `${p}|${z}|${r}: ${stats.total}场(胜${stats.胜}平${stats.平}负${stats.负})\n`;
}

// 更新已有页面
const pageId = '35d91ad7-17ba-8121-8d7a-c89dc7737f72';

const data = JSON.stringify({
    properties: {
        '总场数': { number: total },
        '胜': { number: totalWins },
        '平': { number: totalDraws },
        '负': { number: totalLosses },
        '竞彩正确率': { rich_text: [{ text: { content: `${totalWins}/${total} (${Math.round(totalWins/total*100)}%)` } }] },
        '最大分组': { rich_text: [{ text: { content: `${pred}|${zj}|${rq}` } }] },
        '最大分组详情': { rich_text: [{ text: { content: `${maxStats.total}场: 胜${maxStats.胜} 平${maxStats.平} 负${maxStats.负}` } }] },
        '分组明细': { rich_text: [{ text: { content: detail.trim() } }] }
    }
});

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
    res.on('end', () => {
        try {
            const r = JSON.parse(d);
            console.log('✅ 已更新页面:', r.id);
        } catch (e) {
            console.log('Error:', d);
        }
    });
});
req.on('error', e => console.log('Error:', e.message));
req.write(data);
req.end();
