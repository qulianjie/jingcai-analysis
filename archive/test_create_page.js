const https = require('https');
const fs = require('fs');
const path = require('path');

const keyPath = path.join(require('os').homedir(), '.config', 'notion', 'api_key');
const raw = fs.readFileSync(keyPath);
const token = raw.toString('utf16le').replace(/\0/g, '').trim();

const DATABASE_ID = '36191ad717ba80beb656cc7c0baaa33d';
const DATA_SOURCE_ID = '36191ad7-17ba-8035-b6b5-000b5cc849af';

// Try creating a page via data source
const data = JSON.stringify({
    parent: { database_id: DATABASE_ID },
    properties: {
        Name: { title: [{ text: { content: 'Test Report' } }] },
    },
    children: [
        {
            object: 'block',
            type: 'paragraph',
            paragraph: {
                rich_text: [{ type: 'text', text: { content: 'Test content' } }]
            }
        }
    ]
});

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
