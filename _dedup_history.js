const https = require('https');
const API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

function queryDB(startCursor) {
    const body = JSON.stringify({
        page_size: 100,
        ...(startCursor ? { start_cursor: startCursor } : {})
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/databases/' + DB_ID + '/query',
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body)
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(JSON.parse(d)));
        });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

function deletePage(pageId) {
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages/' + pageId,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(JSON.parse(d)));
        });
        req.on('error', reject);
        req.write(JSON.stringify({ archived: true }));
        req.end();
    });
}

async function main() {
    console.log('正在拉取所有数据...');
    let allPages = [];
    let cursor = null;
    do {
        const resp = await queryDB(cursor);
        allPages = allPages.concat(resp.results);
        cursor = resp.has_more ? resp.next_cursor : null;
    } while (cursor);
    console.log('总页面数: ' + allPages.length);

    // 提取字段 + 建组合主键
    const groups = {};
    for (const p of allPages) {
        const props = p.properties;
        const date = props['日期']?.date?.start || '无日期';
        const jingcai = props['竞彩']?.select?.name || '无';
        const zhuangjia = props['庄家']?.select?.name || '无';
        const rangqiu = props['让球']?.select?.name || '无';
        
        // 组合主键：日期|竞彩|庄家|让球
        const key = date + '|' + jingcai + '|' + zhuangjia + '|' + rangqiu;
        if (!groups[key]) groups[key] = [];
        groups[key].push({ id: p.id, date, jingcai, zhuangjia, rangqiu });
    }

    // 找重复
    const dups = [];
    let uniqueCount = 0;
    for (const [key, items] of Object.entries(groups)) {
        if (items.length > 1) {
            dups.push({ key, items });
        } else {
            uniqueCount++;
        }
    }

    console.log('唯一组合: ' + uniqueCount);
    console.log('重复组合: ' + dups.length);

    if (dups.length === 0) {
        console.log('没有重复，退出');
        return;
    }

    // 打印重复详情（前5组）
    console.log('\n重复详情（前5组）:');
    dups.slice(0, 5).forEach((d, i) => {
        console.log('\n[' + (i+1) + '] Key: ' + d.key);
        d.items.forEach((item, j) => {
            console.log('  [' + (j+1) + '] ' + item.id + ' | ' + item.date + ' | ' + item.jingcai + ' | ' + item.zhuangjia + ' | ' + item.rangqiu);
        });
    });

    // 删除重复（每组保留第一条，删掉其余）
    console.log('\n开始删除重复项...');
    let delCount = 0;
    for (const d of dups) {
        for (let i = 1; i < d.items.length; i++) {
            try {
                await deletePage(d.items[i].id);
                delCount++;
                console.log('[删除] ' + d.items[i].id + ' — ' + d.key);
            } catch (e) {
                console.error('[失败] ' + d.items[i].id + ': ' + e.message);
            }
            await new Promise(r => setTimeout(r, 200));
        }
    }

    console.log('\n[DONE] 共删除 ' + delCount + ' 条重复，保留 ' + uniqueCount + ' 条唯一记录');
}

main().catch(e => { console.error(e); process.exit(1); });
