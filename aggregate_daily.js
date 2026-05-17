const https = require('https');

const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-802f-acb7-ebfd74db132c';

// 先查询历史每日汇总的所有记录
const data = JSON.stringify({ page_size: 100 });

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/35d91ad7-17ba-80fb-a45c-cb6471eaf4d9/query',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
}, res => {
    let d = '';
    res.on('data', c => d += c);
    res.on('end', () => {
        const r = JSON.parse(d);
        console.log('历史每日汇总记录:', r.results.length);
        
        // 按 竞彩|庄家|让球 分组汇总
        const agg = {};
        for (const page of r.results) {
            const props = page.properties;
            const jp = props['竞彩']?.select?.name || '未知';
            const zj = props['庄家']?.select?.name || '未知';
            const rq = props['让球']?.select?.name || '未知';
            const count = props['场数']?.number || 0;
            const wins = props['胜']?.number || 0;
            const draws = props['平']?.number || 0;
            const losses = props['负']?.number || 0;
            
            const key = `${jp}|${zj}|${rq}`;
            if (!agg[key]) agg[key] = { total: 0, wins: 0, draws: 0, losses: 0 };
            agg[key].total += count;
            agg[key].wins += wins;
            agg[key].draws += draws;
            agg[key].losses += losses;
        }
        
        console.log('汇总分组数:', Object.keys(agg).length);
        for (const [k, v] of Object.entries(agg).sort((a,b) => b[1].total - a[1].total)) {
            console.log(`  ${k}: ${v.total}场 胜${v.wins} 平${v.draws} 负${v.losses}`);
        }
        
        // 保存到文件供后续使用
        const fs = require('fs');
        fs.writeFileSync('C:/Users/lianjie/.openclaw/workspace/data/jingcai/daily_agg.json', JSON.stringify(agg, null, 2));
        console.log('\n已保存到 daily_agg.json');
    });
});
req.write(data);
req.end();
