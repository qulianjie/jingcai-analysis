// Delete entries from old DB and archive unused pages
const https = require('https');
const key = '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';
const dsId = '463d8f65-411c-480d-bcc9-e16c4715497c';

function notionRequest(method, path, body) {
    return new Promise((resolve, reject) => {
        const data = body ? JSON.stringify(body) : null;
        const opts = {
            hostname: 'api.notion.com',
            path: path,
            method: method,
            headers: {
                'Authorization': 'Bearer ' + key,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json'
            },
            timeout: 30000
        };
        if (data) {
            opts.headers['Content-Length'] = Buffer.byteLength(data);
        }
        const req = https.request(opts, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try { resolve(JSON.parse(d)); }
                catch(e) { resolve({ raw: d }); }
            });
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
        if (data) req.write(data);
        req.end();
    });
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function main() {
    // Step 1: Query old DB entries
    console.log('=== Querying old DB ===');
    const all = await notionRequest('POST', '/v1/data_sources/' + dsId + '/query', { page_size: 100 });
    const results = all.results || [];
    
    const yesterday = results.filter(i => i.properties?.比赛日期?.date?.start === '2026-05-02');
    const today = results.filter(i => i.properties?.比赛日期?.date?.start === '2026-05-03');
    
    console.log('Yesterday (5/2):', yesterday.length);
    console.log('Today (5/3):', today.length);
    
    // Step 2: Delete yesterday's entries
    console.log('\n=== Deleting yesterday\'s entries ===');
    let deletedCount = 0;
    for (const entry of yesterday) {
        const num = entry.properties?.竞彩编号?.rich_text?.[0]?.plain_text || '?';
        try {
            await notionRequest('PATCH', '/v1/pages/' + entry.id, { archived: true });
            console.log('Deleted:', num);
            deletedCount++;
        } catch(e) {
            console.log('Failed to delete:', num, e.message);
        }
        await sleep(500);
    }
    console.log('\nDeleted yesterday entries:', deletedCount + '/' + yesterday.length);
    
    // Step 3: Handle today's duplicates (keep last created)
    console.log('\n=== Handling today\'s duplicates ===');
    const byNum = {};
    today.forEach(i => {
        const num = i.properties?.竞彩编号?.rich_text?.[0]?.plain_text || '';
        if (!byNum[num]) byNum[num] = [];
        byNum[num].push(i);
    });
    
    for (const [num, entries] of Object.entries(byNum)) {
        if (entries.length > 1) {
            console.log('Duplicate', num, ':', entries.length, 'entries');
            // Keep the last one, delete the rest
            const toDelete = entries.slice(0, -1);
            for (const entry of toDelete) {
                try {
                    await notionRequest('PATCH', '/v1/pages/' + entry.id, { archived: true });
                    console.log('  Deleted dup:', num);
                    deletedCount++;
                } catch(e) {
                    console.log('  Failed to delete dup:', num, e.message);
                }
                await sleep(500);
            }
        }
    }
    
    // Step 4: Archive unused pages (35491ad7 pages)
    console.log('\n=== Archiving unused pages ===');
    const unusedPages = [
        '35491ad7-17ba-818c-aee6-cb777896b9f2',
        '35491ad7-17ba-813e-a791-ebad59f43a7c',
        '35491ad7-17ba-8178-8165-f462c4d3efac',
        '35491ad7-17ba-8174-a292-e206feb7c78f',
        '35491ad7-17ba-812d-91a2-d586a4129548',
        '35491ad7-17ba-81f4-8a95-e323924e56ac',
        '35491ad7-17ba-81cd-b022-e79224cf2d5a',
        '35491ad7-17ba-81ca-b061-f3ba0e380fae',
        '35491ad7-17ba-812b-96be-e05c4dd68f77',
        '35491ad7-17ba-819c-9a0e-f951bbbdb818',
        '35491ad7-17ba-81b3-940a-cef0d1ca3944',
        '35491ad7-17ba-8139-b89f-daed13721e09',
        '35491ad7-17ba-8101-92c2-e56df6350e87',
        '35491ad7-17ba-81b6-bd65-e34285e6e80d'
    ];
    
    for (const pageId of unusedPages) {
        try {
            await notionRequest('PATCH', '/v1/pages/' + pageId, { archived: true });
            console.log('Archived page:', pageId);
        } catch(e) {
            console.log('Failed to archive page:', pageId, e.message);
        }
        await sleep(500);
    }
    
    console.log('\n=== Summary ===');
    console.log('Total deleted:', deletedCount);
    console.log('Done!');
}

main().catch(e => console.error('FAIL:', e.message));
