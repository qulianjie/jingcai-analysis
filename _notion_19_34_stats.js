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

  // 019-034 各自的三向一致条件 + 赔率
  const matches = [
    { num:'019', name:'奥萨苏纳vs西班牙人', win:1.82, pred:'客胜', best:'客胜' },
    { num:'020', name:'毕尔巴鄂vs塞尔塔', win:2.07, pred:'客胜', best:'客胜' },
    { num:'021', name:'奥维耶多vs阿拉维斯', win:3.95, pred:'客胜', best:'主胜' },
    { num:'022', name:'马竞vs赫罗纳', win:1.70, pred:'平局', best:'客胜' },
    { num:'023', name:'莱万特vs马洛卡', win:1.92, pred:'客胜', best:'客胜' },
    { num:'024', name:'巴列卡诺vs比利亚雷', win:2.18, pred:'平局', best:'平局' },
    { num:'025', name:'埃尔切vs赫塔费', win:2.04, pred:'平局', best:'客胜' },
    { num:'026', name:'塞维利亚vs皇马', win:2.90, pred:'客胜', best:'平局' },
    { num:'027', name:'皇家社会vs巴伦西亚', win:2.05, pred:'客胜', best:'平局' },
    { num:'028', name:'萨索洛vs莱切', win:2.45, pred:'客胜', best:'平局' },
    { num:'029', name:'乌迪内斯vs克雷莫纳', win:2.20, pred:'客胜', best:'客胜' },
    { num:'030', name:'里昂vs朗斯', win:1.67, pred:'客胜', best:'平局' },
    { num:'031', name:'里尔vs欧塞尔', win:1.30, pred:'客胜', best:'客胜' },
    { num:'032', name:'马赛vs雷恩', win:1.89, pred:'客胜', best:'平局' },
    { num:'033', name:'巴萨vs贝蒂斯', win:1.25, pred:'主胜', best:'平局' },
    { num:'034', name:'纳什维尔vs洛杉矶FC', win:2.16, pred:'客胜', best:'客胜' },
  ];

  for (const tp of matches) {
    // 收集所有满足条件的历史比赛
    let matched = [];

    for (const p of hasFB) {
      const props = p.properties;
      const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const winOdd = props['竞彩欧赔胜']?.number || 0;
      const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
      const correct = props['预测正确']?.checkbox;
      const name = props['Name']?.title?.[0]?.plain_text || '';
      const date = props['比赛日期']?.date?.start || '';

      let pd='', bd='';
      for(const k of ['主胜','平局','客胜']) { if(predRaw.includes(k)) pd=k; if(bestRaw.includes(k)) bd=k; }

      // 条件: 胜赔±0.1 + 竞彩预测方向 + 庄家看好方向
      if (Math.abs(winOdd - tp.win) > 0.1) continue;
      if (pd !== tp.pred) continue;
      if (bd !== tp.best.replace('让球','')) continue;

      const parts = score.split(':');
      let result = '';
      if (parts.length === 2) {
        const h = parseInt(parts[0]), a = parseInt(parts[1]);
        if (h > a) result = '主胜';
        else if (h === a) result = '平局';
        else result = '客胜';
      }

      matched.push({ correct, result, name, score, date });
    }

    const st = matched.length;
    const correct = matched.filter(x => x.correct === true).length;
    let wc=0, dc=0, lc=0;
    for (const m of matched) {
      if (m.result === '主胜') wc++;
      else if (m.result === '平局') dc++;
      else if (m.result === '客胜') lc++;
    }

    console.log('--- ' + tp.num + ' ' + tp.name + ' ---');
    console.log('  条件: 赔率≈' + tp.win.toFixed(2) + ' + 预测=' + tp.pred + ' + 庄家看好=' + tp.best);
    console.log('  历史匹配: ' + st + ' 场');
    if (st > 0) {
      console.log('  准确率: ' + correct + '/' + st + ' (' + (correct/st*100).toFixed(0) + '%)');
      console.log('  实际: 主胜' + wc + ' (' + (wc/st*100).toFixed(0) + '%)  平' + dc + ' (' + (dc/st*100).toFixed(0) + '%)  客胜' + lc + ' (' + (lc/st*100).toFixed(0) + '%)');
      matched.slice(-3).forEach(x => console.log('    ' + (x.correct?'✅':'❌') + ' ' + x.name + ' ' + x.score));
    } else {
      console.log('  无匹配数据');
    }
    console.log();
  }
}
main().catch(e => console.error(e));
