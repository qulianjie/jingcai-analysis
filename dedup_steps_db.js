// Deduplicate the 26-steps Notion database
// Keep the latest page per "比赛" title, delete older duplicates
const https = require('https');
const NOTION_API_KEY = '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';
const DB_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body || ''),
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
        catch (e) { resolve({ status: res.statusCode, data: d }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

// Query all pages in the database
async function queryAllPages() {
  const pages = [];
  let cursor = null;
  do {
    const endpoint = cursor
      ? `/v1/databases/${DB_ID}/query?filter[property]=比赛&sorts[0]=property=比赛&sorts[0]=direction=descending&start_cursor=${cursor}`
      : `/v1/databases/${DB_ID}/query`;
    const r = await notionRequest('POST', endpoint, {
      page_size: 100,
      sorts: [{ timestamp: 'created_time', direction: 'descending' }],
    });
    if (r.status === 200) {
      pages.push(...r.data.results);
      cursor = r.data.has_more ? r.data.next_cursor : null;
    } else {
      console.error('Query error:', r.status, JSON.stringify(r.data).substring(0, 200));
      break;
    }
  } while (cursor);
  return pages;
}

function getRichTextValue(page, propName) {
  const prop = page.properties[propName];
  if (!prop) return '';
  if (prop.title && prop.title.length > 0) return prop.title[0].plain_text || '';
  if (prop.rich_text && prop.rich_text.length > 0) return prop.rich_text[0].plain_text || '';
  return '';
}

(async () => {
  console.log('Querying all pages...');
  const pages = await queryAllPages();
  console.log(`Total pages: ${pages.length}`);

  // Group by "比赛" title
  const groups = {};
  for (const page of pages) {
    const title = getRichTextValue(page, '比赛');
    if (!title) continue;
    if (!groups[title]) groups[title] = [];
    groups[title].push(page);
  }

  console.log(`Unique matches: ${Object.keys(groups).length}`);

  // Find duplicates
  const duplicates = [];
  for (const [title, pages] of Object.entries(groups)) {
    if (pages.length > 1) {
      // Sort by created time, keep the latest
      pages.sort((a, b) => new Date(b.created_time) - new Date(a.created_time));
      // Keep first (latest), delete rest
      for (let i = 1; i < pages.length; i++) {
        duplicates.push({ title, pageId: pages[i].id, created: pages[i].created_time });
      }
    }
  }

  console.log(`Duplicates to delete: ${duplicates.length}`);
  if (duplicates.length === 0) {
    console.log('No duplicates found.');
    return;
  }

  // Show first 10 duplicates
  for (const d of duplicates.slice(0, 10)) {
    console.log(`  [${d.title}] page=${d.pageId} created=${d.created}`);
  }
  if (duplicates.length > 10) {
    console.log(`  ... and ${duplicates.length - 10} more`);
  }

  // Delete duplicates (archive them)
  console.log('\nDeleting duplicates...');
  let deleted = 0;
  for (const d of duplicates) {
    const r = await notionRequest('PATCH', `/v1/pages/${d.pageId}`, { archived: true });
    if (r.status === 200) {
      deleted++;
      console.log(`  Deleted: ${d.title}`);
    } else {
      console.log(`  Failed: ${d.title} (${r.status})`);
    }
  }
  console.log(`\nDone! Deleted ${deleted}/${duplicates.length} duplicates.`);
})();
