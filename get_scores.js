const https = require('https');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-818d-b7cc-d8a433d05229';

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
    // Get database info
    const info = await notionReq('GET', `/v1/databases/${DB_ID}`);
    console.log('Database props:', Object.keys(info.data.properties || {}).join(', '));
    
    // Query all records
    let all = [];
    let cursor = null;
    do {
        const body = { page_size: 100 };
        if (cursor) body.start_cursor = cursor;
        const res = await notionReq('POST', `/v1/databases/${DB_ID}/query`, body);
        all = all.concat(res.data.results || []);
        cursor = res.data.has_more ? res.data.next_cursor : null;
    } while (cursor);
    
    console.log(`Total records: ${all.length}`);
    
    // Extract scores
    const scoreMap = {};
    for (const page of all) {
        const p = page.properties;
        let matchNum = '', score = '', pred = '', handicap = '', rqPred = '';
        
        for (const [k, v] of Object.entries(p)) {
            if (v.type === 'rich_text' && v.rich_text?.length > 0) {
                const txt = v.rich_text[0].plain_text;
                if (txt.includes('周')) matchNum = txt;
                if (k.includes('比分') || k.includes('score')) score = txt;
                if (k.includes('预测') && !k.includes('让球')) pred = txt;
                if (k.includes('让球预测')) rqPred = txt;
            }
        }
        
        if (matchNum) {
            scoreMap[matchNum] = { score, pred, rqPred };
            if (score) {
                console.log(`${matchNum}: 比分${score}, 预测${pred}, 让球预测${rqPred}`);
            }
        }
    }
    
    const withScore = Object.keys(scoreMap).filter(k => scoreMap[k].score).length;
    console.log(`\n有比分的: ${withScore}/${Object.keys(scoreMap).length}`);
    
    // Save for Python
    const fs = require('fs');
    fs.writeFileSync('jingcai/score_map.json', JSON.stringify(scoreMap, null, 2), 'utf8');
    console.log('Saved to jingcai/score_map.json');
}

main().catch(console.error);
