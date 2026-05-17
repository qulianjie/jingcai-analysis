// 验证Notion数据库数据
const https = require('https');
const API_KEY = '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';
const DB_ID = '93490bfb-ac43-49be-a24d-9e3e5a225991';

const data = JSON.stringify({
    filter: { property: '竞彩编号', rich_text: { is_not_empty: true } },
    sorts: [{ property: '竞彩编号', direction: 'ascending' }],
    page_size: 5
});

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DB_ID}/query`,
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2025-09-03',
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
                const num = pr['竞彩编号']?.rich_text?.[0]?.plain_text || '?';
                const home = pr['主队']?.rich_text?.[0]?.plain_text || '?';
                const away = pr['客队']?.rich_text?.[0]?.plain_text || '?';
                const pred = pr['竞彩预测']?.rich_text?.[0]?.plain_text || '(空)';
                const panlu = pr['盘路匹配']?.rich_text?.[0]?.plain_text || '(空)';
                const oupei = pr['欧赔趋势']?.rich_text?.[0]?.plain_text || '(空)';
                const yapan = pr['亚盘趋势']?.rich_text?.[0]?.plain_text || '(空)';
                const rangqiu = pr['让球趋势']?.rich_text?.[0]?.plain_text || '(空)';
                const baijia = pr['百家对比']?.rich_text?.[0]?.plain_text || '(空)';
                
                console.log(`${i+1}. ${num} ${home}vs${away}`);
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
