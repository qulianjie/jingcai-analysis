const https = require('https');
const fs = require('fs');
const path = require('path');

// Read API key (UTF-16 encoded)
const keyPath = path.join(require('os').homedir(), '.config', 'notion', 'api_key');
const raw = fs.readFileSync(keyPath);
const token = raw.toString('utf16le').replace(/\0/g, '').trim();

const DATABASE_ID = '36191ad717ba80beb656cc7c0baaa33d';

function getDatabaseSchema() {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({});
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
                try {
                    const json = JSON.parse(body);
                    const props = json.properties || {};
                    console.log('Database:', json.title?.[0]?.plain_text || 'N/A');
                    console.log('\nProperties:');
                    for (const [name, info] of Object.entries(props)) {
                        console.log(`  ${name}: ${info.type}`);
                    }
                    resolve(json);
                } catch(e) {
                    reject(e);
                }
            });
        });
        req.on('error', reject);
        req.end();
    });
}

getDatabaseSchema().catch(e => console.error(e));
