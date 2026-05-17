const https = require('https');
const fs = require('fs');
const path = require('path');
const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
const DATA_DIR = path.join(__dirname, 'tasks', '2026-05-12', 'data');

// Build matchnum -> dir map
const matchMap = {};
const dataDirs = fs.readdirSync(DATA_DIR);
for (const d of dataDirs) {
    if (!d.startsWith('match')) continue;
    const mp = path.join(DATA_DIR, d, 'meta.json');
    if (fs.existsSync(mp)) {
        const m = JSON.parse(fs.readFileSync(mp, 'utf8'));
        const mn = m.matchnum || '';
        if (mn) matchMap[mn] = { dir: path.join(DATA_DIR, d), meta: m };
    }
}
console.log('构建match映射:', Object.keys(matchMap).length, '个');

// Query Notion
const queryData = JSON.stringify({
    filter: {
        property: '比赛日期',
        date: { on_or_after: '2026-05-12' }
    },
    page_size: 50
});

function queryNotion() {
    return new Promise((resolve, reject) => {
        const req = https.request({
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
                if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + body));
                else resolve(JSON.parse(body));
            });
        });
        req.on('error', reject);
        req.write(queryData);
        req.end();
    });
}

function updatePage(pageId, props) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ properties: props });
        const req = https.request({
            hostname: 'api.notion.com',
            path: '/v1/pages/' + pageId,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let body = '';
            res.on('data', c => body += c);
            res.on('end', () => {
                if (res.statusCode >= 300) reject(new Error('HTTP ' + res.statusCode + ': ' + body));
                else resolve(JSON.parse(body));
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    const r = await queryNotion();
    const pages = r.results || [];
    console.log('Notion找到', pages.length, '场比赛\n');
    
    let updated = 0;
    
    for (const page of pages) {
        const nameField = page.properties.Name?.title?.[0]?.plain_text || '';
        if (nameField.includes('分组统计')) continue;
        
        const matchNum = nameField.match(/^([周][一二三四五六日]\d+)/);
        if (!matchNum) {
            console.log('⚠️ 不匹配:', nameField);
            continue;
        }
        
        const mn = matchNum[1];
        const info = matchMap[mn];
        
        if (!info) {
            console.log('⚠️', mn, '- 未找到match目录');
            continue;
        }
        
        // Extract step4 handicap odds (instant values)
        // Format: | 竞彩官方 | -1 | 初胜 | 初平 | 初负 | 即胜 | 即平 | 即负 |
        // parts:  [0]         [1] [2]   [3]   [4]   [5]   [6]   [7]
        let rq_win = 0, rq_draw = 0, rq_loss = 0;
        const step4Path = path.join(info.dir, 'group02_handicap', 'step4_handicap_base.txt');
        if (fs.existsSync(step4Path)) {
            const c4 = fs.readFileSync(step4Path, 'utf8');
            for (const line of c4.split('\n')) {
                if (!line.includes('|')) continue;
                const parts = line.split('|').map(p => p.trim()).filter(p => p);
                if (parts.length >= 8 && parts[0] === '竞彩官方') {
                    rq_win = parseFloat(parts[5]) || 0;
                    rq_draw = parseFloat(parts[6]) || 0;
                    rq_loss = parseFloat(parts[7]) || 0;
                    break;
                }
            }
        }
        
        // Extract Macau Asian handicap from meta.json
        let macau_line = info.meta.macau_line || '';
        // Fallback: try step6 file if meta doesn't have it
        if (!macau_line) {
            const step6Path = path.join(info.dir, 'group03_asian', 'step6_asian_base.txt');
            if (fs.existsSync(step6Path)) {
                const c6 = fs.readFileSync(step6Path, 'utf8');
                for (const line of c6.split('\n')) {
                    if (!line.includes('澳门')) continue;
                    const parts = line.split('|').map(p => p.trim()).filter(p => p);
                    if (parts.length >= 3) {
                        macau_line = parts[parts.length - 1] || '';
                    }
                    break;
                }
            }
        }
        
        const props = {
            '让球指数胜': { number: rq_win },
            '让球指数平': { number: rq_draw },
            '让球指数负': { number: rq_loss },
        };
        if (macau_line) {
            props['竞彩澳门亚盘'] = { rich_text: [{ text: { content: macau_line } }] };
        }
        
        await updatePage(page.id, props);
        updated++;
        
        console.log('✅', mn, nameField.replace(mn + ' ', ''),
            '| 让球:', (rq_win || '-').toFixed(2), (rq_draw || '-').toFixed(2), (rq_loss || '-').toFixed(2),
            '| 澳门亚盘:', macau_line || '(空)');
    }
    
    console.log('\n完成！更新了', updated, '场比赛');
}

main().catch(e => console.error(e));
