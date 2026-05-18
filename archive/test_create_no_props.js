const https = require('https');
const fs = require('fs');
const path = require('path');

const keyPath = path.join(require('os').homedir(), '.config', 'notion', 'api_key');
const raw = fs.readFileSync(keyPath);
const token = raw.toString('utf16le').replace(/\0/g, '').trim();

const DATABASE_ID = '36191ad717ba80beb656cc7c0baaa33d';

// Try creating a page with just parent (no properties)
const data = JSON.stringify({
    parent: { database_id: DATABASE_ID },
    children: [
        {
            object: 'block',
            type: 'heading_1',
            heading_1: {
                rich_text: [{ type: 'text', text: { content: 'Test Report' } }]
            }
        },
        {
            object: 'block',
            type: 'paragraph',
            paragraph: {
                rich_text: [{ type: 'text', text: { content: 'Test content for 文档中心' } }]
            }
        }
    ]
});

console.log('Creating page in 文档中心...');

const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/pages',
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
    }
}, res => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Body:', body);
    });
});
req.on('error', e => console.error(e));
req.write(data);
req.end();
