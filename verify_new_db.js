// 验证新数据库数据
const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const data = JSON.stringify({ page_size: 5, sorts: [{ property: '比赛', direction: 'ascending' }] });

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
    res.on('end', () => {
        if (res.statusCode === 200) {
            const r = JSON.parse(d);
            console.log('共', r.results?.length || 0, '条\n');
            (r.results || []).forEach((p, i) => {
                const pr = p.properties;
                const match = pr['比赛']?.rich_text?.[0]?.plain_text || '?';
                const pred = pr['竞彩预测']?.rich_text?.[0]?.plain_text || '(空)';
                const panlu = pr['盘路匹配']?.rich_text?.[0]?.plain_text || '(空)';
                const oupei = pr['欧赔趋势']?.rich_text?.[0]?.plain_text || '(空)';
                const yapan = pr['亚盘趋势']?.rich_text?.[0]?.plain_text || '(空)';
                const rangqiu = pr['让球趋势']?.rich_text?.[0]?.plain_text || '(空)';
                const baijia = pr['百家对比']?.rich_text?.[0]?.plain_text || '(空)';
                
                console.log(`${i+1}. ${match}`);
                console.log(`   预测: ${pred}`);
                console.log(`   盘路: ${panlu}`);
                console.log(`   欧赔: ${oupei}`);
                console.log(`   让球: ${rangqiu}`);
                console.log(`   亚盘: ${yapan}`);
                console.log(`   百家: ${baijia}`);
                console.log('');
            });
        } else {
            console.log('Error:', res.statusCode, d.substring(0, 500));
        }
    });
});
req.on('error', e => console.error('Error:', e.message));
req.write(data);
req.end();
