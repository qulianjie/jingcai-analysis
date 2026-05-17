const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function notionReq(method, path, body) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body || '');
        const req = https.request({
            hostname: 'api.notion.com',
            path: path,
            method: method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => resolve({ status: res.statusCode, data: JSON.parse(b) }));
        });
        req.on('error', reject);
        if (body) req.write(data);
        req.end();
    });
}

async function main() {
    console.log('从Notion拉取比分...\n');
    
    // Get all records
    let all = [];
    let cursor = null;
    do {
        const body = { page_size: 100 };
        if (cursor) body.start_cursor = cursor;
        const res = await notionReq('POST', `/v1/databases/${DB_ID}/query`, body);
        all = all.concat(res.data.results || []);
        cursor = res.data.has_more ? res.data.next_cursor : null;
        if (res.status >= 400) break;
    } while (cursor);
    
    console.log(`Total records: ${all.length}\n`);
    
    // Extract scores
    const scoreMap = {};
    for (const page of all) {
        const p = page.properties;
        let matchNum = '', score = '';
        
        for (const [k, v] of Object.entries(p)) {
            if (v.type === 'rich_text' && v.rich_text?.length > 0) {
                const txt = v.rich_text[0].plain_text;
                if (txt && txt.includes('周') && txt.match(/周[一二三四五六日]\d+/)) {
                    matchNum = txt.match(/周[一二三四五六日]\d+/)[0];
                }
                if ((k.includes('比分') || k.includes('score')) && txt && txt.match(/\d+:\d+/)) {
                    score = txt;
                }
            }
        }
        
        if (matchNum && score) {
            scoreMap[matchNum] = score;
        }
    }
    
    console.log(`有比分的: ${Object.keys(scoreMap).length}场\n`);
    for (const [k, v] of Object.entries(scoreMap).sort()) {
        console.log(`  ${k}: ${v}`);
    }
    
    // 写入meta.json
    const BASE = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks';
    let updated = 0;
    
    for (const d of fs.readdirSync(BASE).sort()) {
        const dp = path.join(BASE, d);
        if (!fs.statSync(dp).isDirectory()) continue;
        const dataDir = path.join(dp, 'data');
        if (!fs.existsSync(dataDir)) continue;
        
        let dateUpdated = 0;
        for (const m of fs.readdirSync(dataDir).sort()) {
            if (!m.startsWith('match')) continue;
            const metaPath = path.join(dataDir, m, 'meta.json');
            if (!fs.existsSync(metaPath)) continue;
            
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            const matchnum = meta.matchnum || '';
            
            if (scoreMap[matchnum]) {
                meta.score = scoreMap[matchnum];
                fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
                updated++;
                dateUpdated++;
            }
        }
        if (dateUpdated > 0) console.log(`  ${d}: 更新${dateUpdated}场`);
    }
    
    console.log(`\n总更新: ${updated}场`);
}

main().catch(console.error);
