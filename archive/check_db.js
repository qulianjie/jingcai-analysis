// Check Notion database structure
const https = require('https');
const key = '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';
const targetDbId = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

function notionGet(path) {
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'api.notion.com',
            path: path,
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + key,
                'Notion-Version': '2025-09-03'
            }
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve(JSON.parse(d)));
        });
        req.on('error', reject);
        req.end();
    });
}

async function main() {
    console.log('=== Target Database Structure ===');
    const db = await notionGet('/v1/databases/' + targetDbId);
    console.log('Title:', db.title?.[0]?.plain_text || 'Untitled');
    console.log('Object:', db.object);
    if (db.properties) {
        Object.entries(db.properties).forEach(([k, v]) => {
            console.log('  - ' + k + ' (' + v.type + ')');
        });
    }
}

main().catch(console.error);
