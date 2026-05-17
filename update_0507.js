const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const scores = {
    '周四001': { hs: 2, as: 1 },
    '周四002': { hs: 2, as: 0 },
    '周四003': { hs: 1, as: 0 },
    '周四004': { hs: 0, as: 1 },
    '周四005': { hs: 0, as: 0 },
    '周四006': { cancelled: true }
};

const queryData = JSON.stringify({
    filter: { property: '比赛日期', date: { equals: '2026-05-07' } },
    page_size: 100
});

const queryReq = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + DB_ID + '/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(queryData)
    }
}, res => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        try {
            const r = JSON.parse(body);
            if (!r.results) { console.log('Error:', body); return; }
            
            let done = 0;
            
            for (const page of r.results) {
                const nameField = page.properties.Name?.title?.[0]?.plain_text || '';
                const nameMatch = nameField.match(/^(周四\d+)/);
                if (!nameMatch) continue;
                
                const matchNum = nameMatch[1];
                const data = scores[matchNum];
                if (!data) continue;
                
                const notionPred = page.properties['竞彩预测']?.rich_text?.[0]?.plain_text || '';
                
                let score, actualResult, isCorrect, summary;
                
                if (data.cancelled) {
                    score = '中断';
                    actualResult = '';
                    isCorrect = false;
                    summary = '比赛中断取消（麦独立vs弗拉门戈腰斩）';
                } else {
                    score = data.hs + ':' + data.as;
                    if (data.hs > data.as) actualResult = '胜';
                    else if (data.hs < data.as) actualResult = '负';
                    else actualResult = '平';
                    
                    isCorrect = (notionPred.includes('主胜') && actualResult === '胜') ||
                                (notionPred.includes('客胜') && actualResult === '负') ||
                                (notionPred.includes('平局') && actualResult === '平');
                    
                    summary = '竞彩: ' + notionPred + ' → ' + actualResult + ' (' + score + ')';
                }
                
                const updateData = JSON.stringify({
                    properties: {
                        '实际比分': { rich_text: [{ text: { content: score } }] },
                        '实际结果': { rich_text: [{ text: { content: actualResult } }] },
                        '反馈日期': { date: { start: '2026-05-12' } },
                        '反馈总结': { rich_text: [{ text: { content: summary } }] },
                        '预测正确': { checkbox: isCorrect }
                    }
                });
                
                const updateReq = https.request({
                    hostname: 'api.notion.com',
                    path: '/v1/pages/' + page.id,
                    method: 'PATCH',
                    headers: {
                        'Authorization': 'Bearer ' + API_KEY,
                        'Notion-Version': '2022-06-28',
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(updateData)
                    }
                }, res2 => {
                    let b2 = '';
                    res2.on('data', c => b2 += c);
                    res2.on('end', () => {
                        done++;
                        const status = res2.statusCode < 300 ? '✅' : '❌';
                        console.log(status, matchNum, nameField.substring(matchNum.length).trim(), '|', score, '|', actualResult || '(中断)', '| 正确', isCorrect);
                        if (done >= 6) console.log('\n完成！更新了', done, '场比赛');
                    });
                });
                updateReq.write(updateData);
                updateReq.end();
            }
        } catch (e) { console.log('Parse error:', e.message); }
    });
});
queryReq.write(queryData);
queryReq.end();
