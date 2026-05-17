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

  const today = [
    { num:'019', name:'奥萨苏纳vs西班牙人', pred:'客胜', rq:'让球客胜', best:'客胜', win:1.82 },
    { num:'020', name:'毕尔巴鄂vs塞尔塔', pred:'客胜', rq:'让球客胜', best:'客胜', win:2.07 },
    { num:'021', name:'奥维耶多vs阿拉维斯', pred:'客胜', rq:'让球主胜', best:'主胜', win:3.95 },
    { num:'022', name:'马竞vs赫罗纳', pred:'平局', rq:'让球客胜', best:'客胜', win:1.70 },
    { num:'023', name:'莱万特vs马洛卡', pred:'客胜', rq:'让球客胜', best:'客胜', win:1.92 },
    { num:'024', name:'巴列卡诺vs比利亚雷', pred:'平局', rq:'让球客胜', best:'平局', win:2.18 },
    { num:'025', name:'埃尔切vs赫塔费', pred:'平局', rq:'让球客胜', best:'客胜', win:2.04 },
    { num:'026', name:'塞维利亚vs皇马', pred:'客胜', rq:'让球主胜', best:'平局', win:2.90 },
    { num:'027', name:'皇家社会vs巴伦西亚', pred:'客胜', rq:'让球客胜', best:'平局', win:2.05 },
    { num:'028', name:'萨索洛vs莱切', pred:'客胜', rq:'让球客胜', best:'平局', win:2.45 },
    { num:'029', name:'乌迪内斯vs克雷莫纳', pred:'客胜', rq:'让球客胜', best:'客胜', win:2.20 },
    { num:'030', name:'里昂vs朗斯', pred:'客胜', rq:'让球客胜', best:'平局', win:1.67 },
    { num:'031', name:'里尔vs欧塞尔', pred:'客胜', rq:'让球客胜', best:'客胜', win:1.30 },
    { num:'032', name:'马赛vs雷恩', pred:'客胜', rq:'让球客胜', best:'平局', win:1.89 },
    { num:'033', name:'巴萨vs贝蒂斯', pred:'主胜', rq:'让球客胜', best:'平局', win:1.25 },
    { num:'034', name:'纳什维尔vs洛杉矶FC', pred:'客胜', rq:'让球客胜', best:'客胜', win:2.16 },
  ];

  for (const tp of today) {
    let strict = [];
    let rqOpen = [];
    let oddsOnly = [];

    for (const p of hasFB) {
      const props = p.properties;
      const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const rqRaw = props['让球预测']?.rich_text?.[0]?.plain_text || '';
      const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const w = props['竞彩欧赔胜']?.number || 0;
      const correct = props['预测正确']?.checkbox;
      const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
      const name = props['Name']?.title?.[0]?.plain_text || '';

      let pd='', bd='';
      for(const k of ['主胜','平局','客胜']) { if(predRaw.includes(k)) pd=k; if(bestRaw.includes(k)) bd=k; }
      let rqd='';
      for(const k of ['让球主胜','让球平局','让球客胜']) { if(rqRaw.includes(k)) rqd=k; }

      if (Math.abs(w - tp.win) > 0.1) continue;
      const entry = { correct, score, name, rqd, pd, bd, win:w };
      
      if (pd === tp.pred && bd === tp.best) {
        rqOpen.push(entry);
        if (rqd === tp.rq) strict.push(entry);
      }
      oddsOnly.push(entry);
    }

    const fmt = (list) => {
      if (list.length === 0) return '无数据';
      const ok = list.filter(x => x.correct === true).length;
      let wc=0, dc=0, lc=0;
      for (const m of list) {
        const p = m.score.split(':');
        if (p.length === 2) { const h=parseInt(p[0]), a=parseInt(p[1]); if(h>a) wc++; else if(h===a) dc++; else lc++; }
      }
      return list.length + '场 准' + ok + '(' + (ok/list.length*100).toFixed(0) + '%) 实:主' + wc + '(' + (wc/list.length*100).toFixed(0) + '%)平' + dc + '(' + (dc/list.length*100).toFixed(0) + '%)客' + lc + '(' + (lc/list.length*100).toFixed(0) + '%)';
    };

    console.log('--- 周日' + tp.num + ' ' + tp.name + ' ---');
    console.log('  赔率≈' + tp.win.toFixed(2) + ' 预测=' + tp.pred + ' 让球=' + tp.rq + ' 庄家=' + tp.best);
    console.log('  四条件: ' + fmt(strict));
    console.log('  三条件: ' + fmt(rqOpen));
    console.log('  仅同赔: ' + fmt(oddsOnly));
    console.log();
  }
}
main().catch(e => console.error(e));
