const https = require('https');
const API_KEY = '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';
const HISTORY_DB = '35d91ad717ba80fba45ccb6471eaf4d9';

const SKIP_NAMES = ['分组统计']; // 保留这些类型的记录

async function queryWithRetry(body, retries = 3) {
  while (retries > 0) {
    try {
      return await new Promise((rs, rj) => {
        const req = https.request({
          hostname: 'api.notion.com',
          path: '/v1/databases/' + HISTORY_DB + '/query',
          method: 'POST',
          timeout: 20000,
          headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
        }, res => { let d = ''; res.on('data', x => d += x); res.on('end', () => { try { rs(JSON.parse(d)); } catch(e) { rj(e); } }); });
        req.write(body); req.end();
        req.on('error', rj);
        req.setTimeout(20000, () => { req.destroy(); rj(new Error('timeout')); });
      });
    } catch (e) {
      if (--retries === 0) throw e;
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}

async function deletePage(pageId) {
  return await new Promise((rs, rj) => {
    const req = https.request({
      hostname: 'api.notion.com',
      path: '/v1/pages/' + pageId,
      method: 'PATCH',
      timeout: 10000,
      headers: { 'Authorization': 'Bearer ' + API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' }
    }, res => { let d = ''; res.on('data', x => d += x); res.on('end', () => { try { rs(JSON.parse(d)); } catch(e) { rs({status:500}); } }); });
    req.write(JSON.stringify({ archived: true }));
    req.end();
    req.on('error', rj);
    req.setTimeout(10000, () => { req.destroy(); rj(new Error('timeout')); });
  });
}

async function getAll() {
  let all = [], cursor;
  while (true) {
    const body = JSON.stringify({ page_size: 100, start_cursor: cursor });
    const r = await queryWithRetry(body);
    all = all.concat(r.results || []);
    cursor = r.next_cursor;
    if (!cursor) break;
    // 小休息一下避免限流
    await new Promise(r => setTimeout(r, 200));
  }
  return all;
}

(async () => {
  console.log('获取所有记录...');
  const all = await getAll();
  console.log('总计:', all.length);

  // 分组
  const groups = {};
  for (const p of all) {
    const name = p.properties['比赛']?.title?.[0]?.plain_text || '无名称';
    // 跳过需要保留的（如分组统计）
    if (SKIP_NAMES.some(s => name.includes(s))) continue;
    if (!groups[name]) groups[name] = [];
    groups[name].push(p);
  }

  // 确定每个组保留哪条
  const toDelete = []; // { name, pageId }
  let keepCount = 0;

  for (const [name, pages] of Object.entries(groups)) {
    if (pages.length <= 1) { keepCount++; continue; }

    // 排序：有比赛时间的优先 > 时间最新 > id最大
    pages.sort((a, b) => {
      const timeA = a.properties['比赛时间']?.date?.start || '';
      const timeB = b.properties['比赛时间']?.date?.start || '';
      
      // 有时间的优先
      if (timeA && !timeB) return -1;
      if (!timeA && timeB) return 1;
      
      // 都有时间，新的优先（保留最新生成的）
      if (timeA && timeB) {
        if (timeA !== timeB) return timeB.localeCompare(timeA);
      }
      
      // ID大的优先（可能是最后生成的）
      return b.id.localeCompare(a.id);
    });

    // 保留第一个，删除其余
    for (let i = 1; i < pages.length; i++) {
      toDelete.push({ name, pageId: pages[i].id });
    }
    keepCount++;
  }

  console.log('\n需保留:', keepCount, '个比赛');
  console.log('需删除:', toDelete.length, '条重复');
  console.log('总计处理后:', keepCount, '条（删除后）');

  // 分批删除，每批50条
  console.log('\n开始删除...');
  let deleted = 0, failed = 0;
  const BATCH_SIZE = 50;

  for (let i = 0; i < toDelete.length; i += BATCH_SIZE) {
    const batch = toDelete.slice(i, i + BATCH_SIZE);
    let batchSuccess = 0, batchFail = 0;

    for (const item of batch) {
      try {
        const result = await deletePage(item.pageId);
        if (result.archived === true || result.object === 'page') {
          batchSuccess++;
        } else {
          batchFail++;
          console.log('  ❌ 删除失败:', item.name, result.status);
        }
      } catch (e) {
        batchFail++;
        console.log('  ❌ 删除异常:', item.name, e.message);
      }
      await new Promise(r => setTimeout(r, 350)); // 限流
    }

    deleted += batchSuccess;
    failed += batchFail;
    console.log(`  [${i + batch.length}/${toDelete.length}] 成功:${batchSuccess} 失败:${batchFail}`);
  }

  console.log('\n=== 完成 ===');
  console.log('成功删除:', deleted);
  console.log('失败:', failed);
  console.log('剩余预计:', keepCount + failed + (all.length - Object.values(groups).flat().length - keepCount));
})();
