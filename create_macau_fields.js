const https = require('https');

const API_KEY = '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';
const DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

const fields = [
    '竞彩澳门亚盘',
    '终盘竞彩澳门亚盘',
];

async function createField(name) {
    const data = JSON.stringify({
        properties: {
            [name]: { rich_text: {} }
        }
    });
    
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: `/v1/databases/${DB_ID}`,
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                if (res.statusCode >= 400) {
                    console.log(`  ⚠️ ${name}: HTTP ${res.statusCode}`);
                } else {
                    console.log(`  ✅ ${name}`);
                }
                resolve();
            });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

(async () => {
    console.log('Creating Macau Asian Handicap fields...');
    for (const field of fields) {
        await createField(field);
    }
    console.log('Done');
    process.exit(0);
})();
