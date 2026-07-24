// Update remarks with pattern matching results via Node.js
const https = require('https');
const fs = require('fs');
const path = require('path');

const TOKEN = "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";
const DS_ID = "35491ad7-17ba-81df-b58c-000ba04f22b7";

async function notion(method, endpoint, body) {
    return new Promise((resolve, reject) => {
        const opts = {
            hostname: 'api.notion.com',
            path: '/v1/' + endpoint,
            method,
            headers: {
                'Authorization': 'Bearer ' + TOKEN,
                'Content-Type': 'application/json',
                'Notion-Version': '2025-09-03'
            }
        };
        const req = https.request(opts, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try { resolve(JSON.parse(d)); }
                catch(e) { resolve({ error: d }); }
            });
        });
        req.on('error', reject);
        if (body) req.write(JSON.stringify(body));
        req.end();
    });
}

async function main() {
    // Load pattern match report
    const reportPath = 'C:/Users/lianjie/.openclaw/workspace/jingcai/learnings/match_patterns_report.json';
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    console.log('Report loaded:', report.total_matches, 'matches,', report.matched, 'matched');

    // Find Notion pages for 2026-07-01
    const query = await notion('POST', 'databases/' + DS_ID + '/query', {
        filter: { property: 'matchdate', date: { equals: '2026-07-01' } }
    });
    if (!query.results) { console.log('Query error:', JSON.stringify(query).slice(0,200)); return; }
    console.log('Found', query.results.length, 'Notion pages');

    // Build map: match_num -> page_id
    const pageMap = {};
    for (const page of query.results) {
        const props = page.properties;
        let matchNum = '';
        if (props.matchnum) matchNum = props.matchnum.title?.[0]?.plain_text || '';
        else if (props.竞彩编号) matchNum = props.竞彩编号.rich_text?.[0]?.plain_text || '';
        if (matchNum) pageMap[matchNum] = page.id;
    }
    console.log('Page map:', JSON.stringify(Object.keys(pageMap)));

    // For each matched match, update remarks
    for (const m of report.matches) {
        const mn = m.match_num;
        const pageId = pageMap[mn];
        if (!pageId) { console.log('No page for', mn); continue; }

        // Build remarks text
        const patterns = m.patterns || [];
        const lines = ['模式匹配结果:'];
        for (const p of patterns.slice(0, 10)) {
            const pred = p.prediction || p.direction || '';
            const conf = p.confidence || p.pct || '';
            const lift = p.lift || '';
            const dims = p.dim_n || '';
            const samples = p.samples || p.count || '';
            lines.push(`${pred} ${conf}% (lift=${lift}, ${dims}维, ${samples}场)`);
        }
        const remarks = lines.join('\\n');

        // Update
        const res = await notion('PATCH', 'pages/' + pageId, {
            properties: {
                remarks: { rich_text: [{ text: { content: remarks } }] }
            }
        });
        if (res.object === 'page') console.log('✓ Updated', mn);
        else console.log('✗ Failed', mn, JSON.stringify(res).slice(0,100));
    }
    console.log('Done');
}

main().catch(e => console.log('Error:', e.message));
