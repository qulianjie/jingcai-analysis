const https = require('https');
const KEY = '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';

async function q(cursor) {
  const body = JSON.stringify({ page_size: 100, start_cursor: cursor || undefined });
  return new Promise(r => {
    const req = https.request({
      hostname: 'api.notion.com',
      path: '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17/query',
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    }, res => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>r(JSON.parse(d))); });
    req.write(body); req.end();
  });
}

async function main() {
  let all = [], cursor = null;
  while (true) {
    const ret = await q(cursor);
    if (!ret.results || ret.results.length === 0) break;
    all = all.concat(ret.results);
    if (ret.has_more && ret.next_cursor) cursor = ret.next_cursor;
    else break;
  }
  
  const hasFB = all.filter(p => (p.properties['反馈总结']?.rich_text?.[0]?.plain_text || '').length > 0);
  console.log('历史总反馈: ' + hasFB.length + ' 场\n');

  const tripleSame = [];
  
  for (const p of hasFB) {
    const props = p.properties;
    const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
    const rqRaw = props['让球预测']?.rich_text?.[0]?.plain_text || '';
    const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
    const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
    const correct = props['预测正确']?.checkbox;
    const name = props['Name']?.title?.[0]?.plain_text || '';
    const date = props['比赛日期']?.date?.start || '';

    // 提取方向
    let pd='', bd='';
    for(const k of ['主胜','平局','客胜']) { if(predRaw.includes(k)) pd=k; if(bestRaw.includes(k)) bd=k; }
    
    // 让球方向: "让球客胜" 或 文本中在"让1球/受让1球"之后出现的胜平负
    let rqd='';
    // 方法1: 精确匹配 "让球主胜" / "让球平局" / "让球客胜"
    for(const k of ['让球主胜','让球平局','让球客胜']) { if(rqRaw.includes(k)) { rqd=k.replace('让球',''); break; } }
    // 方法2: 如果没找到，看文本中最后一个胜平负关键词
    if (!rqd) {
      let lastDir = '';
      for(const k of ['主胜','平局','客胜']) { 
        const idx = rqRaw.lastIndexOf(k);
        if (idx >= 0 && (idx > rqRaw.lastIndexOf(lastDir) || !lastDir)) lastDir = k;
      }
      if (lastDir) rqd = lastDir;
    }
    
    // 三向一致
    if (pd && rqd && bd && pd === rqd && rqd === bd) {
      const parts = score.split(':');
      let result = '';
      if (parts.length === 2) {
        const h = parseInt(parts[0]), a = parseInt(parts[1]);
        if (h > a) result = '主胜';
        else if (h === a) result = '平局';
        else result = '客胜';
      }
      
      tripleSame.push({ pred: pd, result, correct, name, score, date });
    }
  }

  console.log('=== 三向一致（竞彩预测=让球方向=庄家最看好）=== ');
  console.log('共 ' + tripleSame.length + ' 场\n');

  const total = tripleSame.length;
  if (total === 0) {
    // 看看问题在哪
    console.log('调试：取前10条检查提取结果');
    for (const p of hasFB.slice(0,10)) {
      const props = p.properties;
      const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const rqRaw = props['让球预测']?.rich_text?.[0]?.plain_text || '';
      const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const name = props['Name']?.title?.[0]?.plain_text || '';
      
      let pd='', bd='';
      for(const k of ['主胜','平局','客胜']) { if(predRaw.includes(k)) pd=k; if(bestRaw.includes(k)) bd=k; }
      
      let rqd='';
      for(const k of ['让球主胜','让球平局','让球客胜']) { if(rqRaw.includes(k)) { rqd=k.replace('让球',''); break; } }
      if (!rqd) {
        for(const k of ['主胜','平局','客胜']) { if(rqRaw.includes(k)) rqd=k; }
      }
      
      console.log(name + ' | pd=' + pd + ' | rqd=' + rqd + ' | bd=' + bd);
    }
    return;
  }

  // 整体统计
  const correct = tripleSame.filter(x => x.correct === true).length;
  let winC=0, drawC=0, lossC=0;
  for (const m of tripleSame) {
    if (m.result === '主胜') winC++;
    else if (m.result === '平局') drawC++;
    else if (m.result === '客胜') lossC++;
  }
  
  console.log('【整体】');
  console.log('准确率: ' + correct + '/' + total + ' (' + (correct/total*100).toFixed(1) + '%)');
  console.log('实际: 主胜' + winC + ' (' + (winC/total*100).toFixed(1) + '%)  平' + drawC + ' (' + (drawC/total*100).toFixed(1) + '%)  客胜' + lossC + ' (' + (lossC/total*100).toFixed(1) + '%)');
  console.log();

  // 按预测方向
  console.log('【按预测方向】');
  for (const dir of ['主胜', '平局', '客胜']) {
    const list = tripleSame.filter(x => x.pred === dir);
    if (list.length === 0) continue;
    const ok = list.filter(x => x.correct === true).length;
    let w=0, d=0, l=0;
    for (const m of list) {
      if (m.result === '主胜') w++;
      else if (m.result === '平局') d++;
      else if (m.result === '客胜') l++;
    }
    console.log(dir + '预测 (' + list.length + '场)');
    console.log('  准: ' + ok + '/' + list.length + ' (' + (ok/list.length*100).toFixed(1) + '%)');
    console.log('  实: 主' + w + '(' + (w/list.length*100).toFixed(1) + '%) 平' + d + '(' + (d/list.length*100).toFixed(1) + '%) 客' + l + '(' + (l/list.length*100).toFixed(1) + '%)');
    console.log();
  }

  // 明细
  console.log('【全部明细】');
  tripleSame.sort((a,b) => b.date.localeCompare(a.date) || b.name.localeCompare(a.name));
  for (const m of tripleSame) {
    console.log((m.correct?'✅':'❌') + ' ' + m.date + ' ' + m.name + ' | 预测=' + m.pred + ' | 比分=' + m.score);
  }
}
main().catch(e => console.error(e));
