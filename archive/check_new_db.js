const https = require('https');
const fs = require('fs');
const path = require('path');

const keyPath = path.join(require('os').homedir(), '.config', 'notion', 'api_key');
const raw = fs.readFileSync(keyPath);
const token = raw.toString('utf16le').replace(/\0/g, '').trim();

const DATABASE_ID = '35d91ad717ba80fba45ccb6471eaf4d9';

const req = https.request({
    hostname: 'api.notion.com',
    path: `/v1/databases/${DATABASE_ID}`,
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Notion-Version': '2025-09-03',
    }
}, res => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        const json = JSON.parse(body);
        console.log('Title:', json.title?.[0]?.plain_text || 'N/A');
        console.log('\nProperties:');
        const props = json.properties || {};
        for (const [name, info] of Object.entries(props)) {
            console.log(`  ${name}: ${info.type}`);
        }
        console.log('\nFull response:');
        console.log(JSON.stringify(json, null, 2));
    });
});
req.on('error', e => console.error(e));
req.end();
