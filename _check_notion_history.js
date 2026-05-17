const https = require('https');
const KEY = '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';

async function queryAll() {
  const results = [];
  let start_cursor = null;
  while (true) {
    const body = JSON.stringify({ page_size: 100, start_cursor });
    const ret = await new Promise(r => {
      const req = https.request({
        hostname: 'api.notion.com',
        path: '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17/query',
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
      }, res => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>r(JSON.parse(d))); });
      req.write(body); req.end();
    });
    if (!ret.results || ret.results.length === 0) break;
    results.push(...ret.results);
    if (!ret.has_more) break;
    start_cursor = ret.next_cursor;
  }
  return results;
}

queryAll().then(pages => {
  console.log('总记录: ' + pages.length);
  
  // 过滤有反馈的
  const hasFeedback = pages.filter(p => {
    const fb = p.properties['反馈总结']?.rich_text?.[0]?.plain_text || '';
    return fb.length > 0;
  });
  console.log('有反馈总结: ' + hasFeedback.length);
  
  if (hasFeedback.length === 0) {
    // 看看最早几条有没有feedback相关的其他字段
    console.log('\n查看前3条的有值字段:');
    for (const p of pages.slice(0,3)) {
      const name = p.properties['Name']?.title?.[0]?.plain_text || '';
      const date = p.properties['比赛日期']?.date?.start || '';
      const score = p.properties['实际比分']?.rich_text?.[0]?.plain_text || '';
      const actual = p.properties['实际结果']?.rich_text?.[0]?.plain_text || '';
      const correct = p.properties['预测正确']?.checkbox;
      const fb = p.properties['反馈总结']?.rich_text?.[0]?.plain_text || '';
      console.log('  ' + name + ' | 日期=' + date + ' | 比分=' + score + ' | 实际=' + actual + ' | 正确=' + correct + ' | 反馈=' + (fb ? '有' : '无'));
    }
    return;
  }
  
  let ok = 0, fail = 0;
  let by_pred = {主胜:{ok:0,fail:0},平局:{ok:0,fail:0},客胜:{ok:0,fail:0}};
  let by_league = {};
  let rq_ok = 0, rq_fail = 0;
  let details = [];

  for (const p of hasFeedback) {
    const props = p.properties;
    const name = props['Name']?.title?.[0]?.plain_text || '';
    const pred_raw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
    const correct = props['预测正确']?.checkbox;
    const rq_correct = props['让球预测正确']?.checkbox;
    const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
    const date = props['比赛日期']?.date?.start || '';

    const nameParts = name.split(' ');
    const leagueName = nameParts.length >= 3 ? nameParts[1] : '';

    let pred_dir = '';
    for (const kw of ['主胜', '平局', '客胜']) {
      if (pred_raw.includes(kw)) { pred_dir = kw; break; }
    }

    if (correct === true) { ok++; if (pred_dir) by_pred[pred_dir].ok++; }
    else if (correct === false) { fail++; if (pred_dir) by_pred[pred_dir].fail++; }
    if (rq_correct === true) rq_ok++;
    else if (rq_correct === false) rq_fail++;

    if (leagueName) {
      if (!by_league[leagueName]) by_league[leagueName] = {ok:0,fail:0};
      if (correct === true) by_league[leagueName].ok++;
      else if (correct === false) by_league[leagueName].fail++;
    }
    if (correct !== null) details.push({name, pred_dir, correct, league: leagueName, score, date});
  }

  const total = ok + fail;
  console.log('\n======== 整体统计 ========');
  console.log('总反馈: ' + total + ' 场');
  console.log('正确: ' + ok + ' (' + (ok/total*100).toFixed(1) + '%)');
  console.log('错误: ' + fail + ' (' + (fail/total*100).toFixed(1) + '%)');
  if (rq_ok + rq_fail > 0) console.log('让球预测: ' + rq_ok + '/' + (rq_ok+rq_fail) + ' (' + (rq_ok/(rq_ok+rq_fail)*100).toFixed(1) + '%)');

  console.log('\n======== 按预测方向 ========');
  for (const k of ['主胜', '平局', '客胜']) {
    const o = by_pred[k];
    const t = o.ok + o.fail;
    if (t > 0) console.log(k + '预测: ' + o.ok + '/' + t + ' (' + (o.ok/t*100).toFixed(1) + '%)');
  }

  console.log('\n======== 按联赛（≥3场）=======');
  Object.entries(by_league).sort((a,b) => (b[1].ok+b[1].fail) - (a[1].ok+a[1].fail))
    .forEach(([l,v]) => { const t=v.ok+v.fail; if(t>=3) console.log(l+': '+v.ok+'/'+t+' ('+(v.ok/t*100).toFixed(1)+'%)'); });

  console.log('\n======== 最近10场 ========');
  details.sort((a,b) => b.date.localeCompare(a.date) || b.name.localeCompare(a.name)).slice(0,10)
    .forEach(d => console.log((d.correct?'✅':'❌')+' '+d.name+' 预测='+(d.pred_dir||'-')+' 比分='+d.score));

  console.log('\n======== 按日期 ========');
  const byDate = {};
  for (const d of details) {
    const dt = d.date.substring(0,10);
    if (!byDate[dt]) byDate[dt] = {ok:0,fail:0};
    if (d.correct) byDate[dt].ok++; else byDate[dt].fail++;
  }
  Object.entries(byDate).sort().forEach(([dt,v]) => {
    const t=v.ok+v.fail; console.log(dt+': '+v.ok+'/'+t+' ('+(v.ok/t*100).toFixed(0)+'%)');
  });
}).catch(e => console.error(e));
