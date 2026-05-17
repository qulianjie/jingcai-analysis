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

  // ===== 今天010-018的预测组合 =====
  const todayPatterns = [
    { match: '周日010 哈马比vs马尔默', pred: '主胜', best: '平局' },
    { match: '周日011 福伦丹vs特尔斯达', pred: '客胜', best: '平局' },
    { match: '周日012 海伦芬vs阿贾克斯', pred: '客胜', best: '主胜' },
    { match: '周日013 达姆施塔vs帕德博恩', pred: '主胜', best: '主胜' },
    { match: '周日014 狼队vs富勒姆', pred: '客胜', best: '主胜' },
    { match: '周日015 埃弗顿vs桑德兰', pred: '客胜', best: '平局' },
    { match: '周日016 布伦特vs水晶宫', pred: '平局', best: '客胜' },
    { match: '周日017 亚特兰大vs博洛尼亚', pred: '客胜', best: '平局' },
    { match: '周日018 纽卡斯尔vs西汉姆联', pred: '客胜', best: '平局' },
  ];

  // 从每条历史记录提取竞彩预测方向 + 实际结果
  for (const tp of todayPatterns) {
    const { match, pred: targetPred, best: targetBest } = tp;
    
    // 1) 统计历史中同样 竞彩预测方向 + 庄家看好组合的比赛
    let samePattern = [];
    let samePredOnly = [];
    
    for (const p of hasFB) {
      const props = p.properties;
      const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const correct = props['预测正确']?.checkbox;
      const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
      const name = props['Name']?.title?.[0]?.plain_text || '';
      const date = props['比赛日期']?.date?.start || '';
      
      let pd = '';
      for (const k of ['主胜', '平局', '客胜']) { if (predRaw.includes(k)) { pd = k; break; } }
      
      if (pd && pd === targetPred) samePredOnly.push({ correct, score, name, date, best: bestRaw });
      if (pd && pd === targetPred && bestRaw === targetBest) samePattern.push({ correct, score, name, date });
    }
    
    const st = samePattern.length;
    const correct = samePattern.filter(x => x.correct === true).length;
    const wrong = samePattern.filter(x => x.correct === false).length;
    const unsure = samePattern.filter(x => x.correct === null || x.correct === undefined).length;
    
    console.log('--- ' + match + ' ---');
    console.log('  预测=' + targetPred + ' + 庄家看好=' + targetBest + ' 历史同组合: ' + st + ' 场');
    if (st > 0) {
      console.log('    结果: 正确' + correct + '(' + (correct/st*100).toFixed(0) + '%) 错误' + wrong + '(' + (wrong/st*100).toFixed(0) + '%)');
      console.log('    最后5场:');
      samePattern.slice(-5).forEach(x => console.log('      ' + (x.correct?'✅':'❌') + ' ' + x.name + ' ' + x.score));
    } else {
      // 没有同组合，看仅同预测方向的
      const st2 = samePredOnly.length;
      const c2 = samePredOnly.filter(x => x.correct === true).length;
      const w2 = samePredOnly.filter(x => x.correct === false).length;
      console.log('  ⚠️ 无同组合数据，仅同预测方向(' + targetPred + '): ' + st2 + ' 场');
      if (st2 > 0) {
        console.log('    结果: 正确' + c2 + '(' + (c2/st2*100).toFixed(0) + '%) 错误' + w2 + '(' + (w2/st2*100).toFixed(0) + '%)');
        
        // 按庄家看好分组
        const byBest = {};
        for (const x of samePredOnly) {
          if (!byBest[x.best]) byBest[x.best] = {ok:0,fail:0};
          if (x.correct === true) byBest[x.best].ok++;
          else if (x.correct === false) byBest[x.best].fail++;
        }
        console.log('    按庄家看好细分:');
        for (const [b, v] of Object.entries(byBest)) {
          const t = v.ok + v.fail;
          if (t > 0) console.log('      庄家看好=' + b + ': ' + v.ok + '/' + t + ' (' + (v.ok/t*100).toFixed(0) + '%)');
        }
      }
    }
    console.log();
  }
}
main().catch(e => console.error(e));
