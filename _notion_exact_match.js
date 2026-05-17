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

  // ===== 今天010-018的各场条件 =====
  const todayPatterns = [
    { num:'010', name:'哈马比vs马尔默', pred:'主胜', rq:'让球客胜', best:'平局', win:1.44 },
    { num:'011', name:'福伦丹vs特尔斯达', pred:'客胜', rq:'让球主胜', best:'平局', win:2.54 },
    { num:'012', name:'海伦芬vs阿贾克斯', pred:'客胜', rq:'让球主胜', best:'主胜', win:3.10 },
    { num:'013', name:'达姆施塔vs帕德博恩', pred:'主胜', rq:'让球主胜', best:'主胜', win:3.25 },
    { num:'014', name:'狼队vs富勒姆', pred:'客胜', rq:'让球主胜', best:'主胜', win:3.80 },
    { num:'015', name:'埃弗顿vs桑德兰', pred:'客胜', rq:'让球客胜', best:'平局', win:1.73 },
    { num:'016', name:'布伦特vs水晶宫', pred:'平局', rq:'让球客胜', best:'客胜', win:1.54 },
    { num:'017', name:'亚特兰大vs博洛尼亚', pred:'客胜', rq:'让球客胜', best:'平局', win:1.55 },
    { num:'018', name:'纽卡斯尔vs西汉姆联', pred:'客胜', rq:'让球客胜', best:'平局', win:2.08 },
  ];

  for (const tp of todayPatterns) {
    // 匹配逻辑：胜赔在±0.03范围内 + 竞彩预测方向 + 让球预测（含"让球客胜/让球主胜"等）+ 庄家看好
    let matchList = [];

    for (const p of hasFB) {
      const props = p.properties;
      const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const rqRaw = props['让球预测']?.rich_text?.[0]?.plain_text || '';
      const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const winOdd = props['竞彩欧赔胜']?.number || 0;
      const correct = props['预测正确']?.checkbox;
      const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
      const name = props['Name']?.title?.[0]?.plain_text || '';
      const date = props['比赛日期']?.date?.start || '';

      let pd='', bd='';
      for(const k of ['主胜','平局','客胜']) {
        if(predRaw.includes(k)) pd=k;
        if(bestRaw.includes(k)) bd=k;
      }

      // 条件1: 胜赔匹配（±0.03）
      if (Math.abs(winOdd - tp.win) > 0.03) continue;
      // 条件2: 竞彩预测方向匹配
      if (pd !== tp.pred) continue;
      // 条件3: 让球预测方向匹配（让球预测文本里必须包含"让球客胜"或"让球主胜"等）
      if (!rqRaw.includes(tp.rq)) continue;
      // 条件4: 庄家看好方向匹配
      if (bd !== tp.best) continue;

      matchList.push({ correct, score, name, date });
    }

    const st = matchList.length;
    const correct = matchList.filter(x => x.correct === true).length;

    let winC=0, drawC=0, lossC=0;
    for (const m of matchList) {
      const parts = m.score.split(':');
      if (parts.length === 2) {
        const h = parseInt(parts[0]), a = parseInt(parts[1]);
        if (h > a) winC++;
        else if (h === a) drawC++;
        else lossC++;
      }
    }

    console.log('--- 周日' + tp.num + ' ' + tp.name + ' ---');
    console.log('  条件: 胜赔=' + tp.win + ' 预测=' + tp.pred + ' 让球=' + tp.rq + ' 庄家=' + tp.best);
    console.log('  历史匹配: ' + st + ' 场');
    if (st > 0) {
      console.log('  预测准确率: ' + correct + '/' + st + ' (' + (correct/st*100).toFixed(0) + '%)');
      console.log('  实际赛果: 主胜' + winC + '(' + (winC/st*100).toFixed(0) + '%) 平' + drawC + '(' + (drawC/st*100).toFixed(0) + '%) 客胜' + lossC + '(' + (lossC/st*100).toFixed(0) + '%)');
      matchList.slice(-3).forEach(x => console.log('    ' + (x.correct?'✅':'❌') + ' ' + x.name + ' ' + x.score));
    } else {
      console.log('  ⚠️ 无匹配记录');
    }
    console.log();
  }
}
main().catch(e => console.error(e));
