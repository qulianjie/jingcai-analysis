const https = require('https');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

// Query all pages for a given date
function queryDB(dateStr) {
    const body = JSON.stringify({
        filter: {
            and: [
                { property: '比赛日期', date: { equals: dateStr } }
            ]
        },
        page_size: 100
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

// Update a page with rounded odds
function updatePage(pageId, win, draw, loss) {
    const body = JSON.stringify({
        properties: {
            '竞彩欧赔胜': { number: win },
            '竞彩欧赔平': { number: draw },
            '竞彩欧赔负': { number: loss }
        }
    });
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages/' + pageId,
            method: 'PATCH',
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

async function main() {
    const dates = ['2026-05-09', '2026-05-10', '2026-05-11'];
    
    for (const date of dates) {
        console.log(`\n处理 ${date}...`);
        const resp = await queryDB(date);
        const pages = resp.results || [];
        console.log(`找到 ${pages.length} 条记录`);
        
        let updated = 0;
        for (const page of pages) {
            const props = page.properties;
            const win = props['竞彩欧赔胜']?.number;
            const draw = props['竞彩欧赔平']?.number;
            const loss = props['竞彩欧赔负']?.number;
            
            if (win !== undefined && draw !== undefined && loss !== undefined && win > 0 && draw > 0 && loss > 0) {
                const newWin = Math.floor(win * 10) / 10;
                const newDraw = Math.floor(draw * 10) / 10;
                const newLoss = Math.floor(loss * 10) / 10;
                
                if (newWin !== win || newDraw !== draw || newLoss !== loss) {
                    try {
                        await updatePage(page.id, newWin, newDraw, newLoss);
                        const name = props.Name?.title?.[0]?.plain_text || '';
                        console.log(`  ${name}: ${win}/${draw}/${loss} → ${newWin}/${newDraw}/${newLoss}`);
                        updated++;
                    } catch (e) {
                        console.log(`  失败: ${e.message}`);
                    }
                    await new Promise(r => setTimeout(r, 200));
                }
            }
        }
        console.log(`更新 ${updated} 条`);
    }
    
    console.log('\n[DONE]');
}

main().catch(e => { console.error(e); process.exit(1); });
