const https = require('https');

const API_KEY = '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';

async function queryDB(dbId) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify({ page_size: 100 });
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${dbId}/query`,
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body)
            }
        }, res => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => resolve(JSON.parse(b)));
        });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

async function main() {
    // Try both DB IDs
    const dbs = [
        { id: '35491ad7-17ba-81cc-aa04-ce53f7234e17', name: '竞彩分析(新)' },
        { id: '93490bfb-ac43-49be-a24d-9e3e5a225991', name: '竞彩分析(旧)' },
    ];
    
    for (const db of dbs) {
        try {
            const res = await queryDB(db.id);
            if (res.results && res.results.length > 0) {
                console.log(`\n${db.name} (${db.id}): ${res.results.length} records`);
                
                // Show first record properties
                const first = res.results[0];
                console.log('Properties:', Object.keys(first.properties).join(', '));
                
                // Extract scores
                let withScore = 0;
                const scoreMap = {};
                for (const page of res.results) {
                    const p = page.properties;
                    let matchNum = '', score = '';
                    for (const [k, v] of Object.entries(p)) {
                        if (v.type === 'rich_text' && v.rich_text && v.rich_text.length > 0) {
                            const txt = v.rich_text[0].plain_text;
                            if (txt && txt.includes('周')) matchNum = txt;
                            if (k.includes('比分') && txt) score = txt;
                        }
                    }
                    if (matchNum && score) {
                        scoreMap[matchNum] = score;
                        withScore++;
                    }
                }
                
                console.log(`有比分的: ${withScore}/${res.results.length}`);
                for (const [k, v] of Object.entries(scoreMap).sort()) {
                    console.log(`  ${k}: ${v}`);
                }
            } else {
                console.log(`${db.name}: 0 records (${res.status || 'ok'})`);
            }
        } catch (e) {
            console.log(`${db.name}: Error - ${e.message}`);
        }
    }
}

main();
