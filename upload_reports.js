const https = require('https');
const fs = require('fs');
const path = require('path');

// Read API key (UTF-16 encoded)
const keyPath = path.join(require('os').homedir(), '.config', 'notion', 'api_key');
const raw = fs.readFileSync(keyPath);
const token = raw.toString('utf16le').replace(/\0/g, '').trim();

const DATABASE_ID = '36191ad717ba80beb656cc7c0baaa33d';

function createPage(title, content) {
    return new Promise((resolve, reject) => {
        // Build Notion blocks from markdown
        const blocks = markdownToBlocks(content);
        
        const data = JSON.stringify({
            parent: { database_id: DATABASE_ID },
            properties: {
                '文档名称': { title: [{ text: { content: title } }] },
                '类别': { multi_select: [{ name: 'match' }] },
            },
            children: blocks,
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
                if (res.statusCode === 200) {
                    const json = JSON.parse(body);
                    resolve(json.id);
                } else {
                    console.error('Error:', res.statusCode, body);
                    resolve(null);
                }
            });
        });
        req.on('error', e => {
            console.error('Request error:', e.message);
            resolve(null);
        });
        req.write(data);
        req.end();
    });
}

function markdownToBlocks(md, maxPerBlock = 1900) {
    const blocks = [];
    const lines = md.split('\n');
    let currentText = '';
    
    for (const line of lines) {
        // Handle headings
        if (line.startsWith('# ')) {
            if (currentText) {
                pushParagraph(blocks, currentText, maxPerBlock);
                currentText = '';
            }
            blocks.push({
                object: 'block',
                type: 'heading_1',
                heading_1: { rich_text: [{ type: 'text', text: { content: line.slice(2).trim() } }] }
            });
        } else if (line.startsWith('## ')) {
            if (currentText) {
                pushParagraph(blocks, currentText, maxPerBlock);
                currentText = '';
            }
            blocks.push({
                object: 'block',
                type: 'heading_2',
                heading_2: { rich_text: [{ type: 'text', text: { content: line.slice(3).trim() } }] }
            });
        } else if (line.startsWith('### ')) {
            if (currentText) {
                pushParagraph(blocks, currentText, maxPerBlock);
                currentText = '';
            }
            blocks.push({
                object: 'block',
                type: 'heading_3',
                heading_3: { rich_text: [{ type: 'text', text: { content: line.slice(4).trim() } }] }
            });
        } else {
            currentText += (currentText ? '\n' : '') + line;
        }
        
        // Limit blocks to avoid API limit
        if (blocks.length >= 95) {
            break;
        }
    }
    
    if (currentText && blocks.length < 95) {
        pushParagraph(blocks, currentText, maxPerBlock);
    }
    
    return blocks;
}

function pushParagraph(blocks, text, maxPerBlock) {
    // Split long text into chunks
    for (let i = 0; i < text.length && blocks.length < 95; i += maxPerBlock) {
        const chunk = text.slice(i, i + maxPerBlock);
        blocks.push({
            object: 'block',
            type: 'paragraph',
            paragraph: { rich_text: [{ type: 'text', text: { content: chunk } }] }
        });
    }
}

async function main() {
    // Find all report files (5月7日以后)
    const tasksDir = 'jingcai/tasks';
    const startDate = new Date('2026-05-07');
    const today = new Date();
    
    const reports = [];
    
    for (let d = new Date(startDate); d <= today; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().slice(0, 10);
        const dateDir = path.join(tasksDir, dateStr);
        
        if (!fs.existsSync(dateDir)) continue;
        
        const files = fs.readdirSync(dateDir);
        for (const f of files) {
            if (f.endsWith('.md') && f !== 'final_report.md' && f !== 'sunday_matches.md') {
                reports.push({
                    date: dateStr,
                    name: f.replace(/\.md$/, ''),
                    path: path.join(dateDir, f),
                });
            }
        }
    }
    
    console.log(`Found ${reports.length} reports\n`);
    
    let success = 0;
    let failed = 0;
    
    for (const report of reports) {
        process.stdout.write(`${report.date}: ${report.name.slice(0, 30)}... `);
        
        const content = fs.readFileSync(report.path, 'utf-8');
        const pageId = await createPage(report.name, content);
        
        if (pageId) {
            console.log(`OK (${pageId.slice(16, 24)})`);
            success++;
        } else {
            console.log('FAIL');
            failed++;
        }
        
        // Rate limit
        await new Promise(r => setTimeout(r, 500));
    }
    
    console.log(`\nDone! Success: ${success}, Failed: ${failed}`);
}

main().catch(e => console.error(e));
