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
    { num:'010', name:'哈马比vs马尔默', pred:'主胜', rq:'让球客胜', best:'平局', win:1.44, draw:4.20, loss:5.10 },
    { num:'011', name:'福伦丹vs特尔斯达', pred:'客胜', rq:'让球主胜', best:'平局', win:2.54, draw:3.46, loss:2.24 },
    { num:'012', name:'海伦芬vs阿贾克斯', pred:'客胜', rq:'让球主胜', best:'主胜', win:3.10, draw:3.93, loss:1.81 },
    { num:'013', name:'达姆施塔vs帕德博恩', pred:'主胜', rq:'让球主胜', best:'主胜', win:3.25, draw:3.95, loss:1.76 },
    { num:'014', name:'狼队vs富勒姆', pred:'客胜', rq:'让球主胜', best:'主胜', win:3.80, draw:3.55, loss:1.71 },
    { num:'015', name:'埃弗顿vs桑德兰', pred:'客胜', rq:'让球客胜', best:'平局', win:1.73, draw:3.37, loss:3.95 },
    { num:'016', name:'布伦特vs水晶宫', pred:'平局', rq:'让球客胜', best:'客胜', win:1.54, draw:3.85, loss:4.55 },
    { num:'017', name:'亚特兰大vs博洛尼亚', pred:'客胜', rq:'让球客胜', best:'平局', win:1.55, draw:3.85, loss:4.45 },
    { num:'018', name:'纽卡斯尔vs西汉姆联', pred:'客胜', rq:'让球客胜', best:'平局', win:2.08, draw:3.45, loss:2.79 },
  ];

  for (const tp of today) {
    let strict = [];   // 胜赔±0.1 + 预测 + 让球 + 庄家
    let rqOpen = [];   // 胜赔±0.1 + 预测 + 庄家（排除让球）
    let oddsOnly = []; // 胜赔±0.1（只看胜赔，其他不管）

    for (const p of hasFB) {
      const props = p.properties;
      const predRaw = props['竞彩预测']?.rich_text?.[0]?.plain_text || '';
      const rqRaw = props['让球预测']?.rich_text?.[0]?.plain_text || '';
      const bestRaw = props['步26_庄家最看好']?.rich_text?.[0]?.plain_text || '';
      const w = props['竞彩欧赔胜']?.number || 0;
      const dr = props['竞彩欧赔平']?.number || 0;
      const l = props['竞彩欧赔负']?.number || 0;
      const correct = props['预测正确']?.checkbox;
      const score = props['实际比分']?.rich_text?.[0]?.plain_text || '';
      const name = props['Name']?.title?.[0]?.plain_text || '';
      const date = props['比赛日期']?.date?.start || '';

      // 方向提取
      let pd='', bd='';
      for(const k of ['主胜','平局','客胜']) { if(predRaw.includes(k)) pd=k; if(bestRaw.includes(k)) bd=k; }
      let rqd='';
      for(const k of ['让球主胜','让球平局','让球客胜']) { if(rqRaw.includes(k)) rqd=k; }

      // 胜赔±0.1
      if (Math.abs(w - tp.win) > 0.1) continue;
      
      // 全部存储
      const entry = { correct, score, name, date, rqd, pd, bd, win:w };
      
      // 胜赔+预测+庄家
      if (pd === tp.pred && bd === tp.best) {
        rqOpen.push(entry);
        // +让球
        if (rqd === tp.rq) strict.push(entry);
      }
      
      oddsOnly.push(entry);
    }

    // 输出
    console.log('--- 周日' + tp.num + ' ' + tp.name + ' ---');
    console.log('  赔率=' + tp.win + '/' + tp.draw + '/' + tp.loss + ' 预测=' + tp.pred + ' 让球=' + tp.rq + ' 庄家=' + tp.best);

    [['四条件精确', strict], ['三条件(排除让球)', rqOpen], ['仅同胜赔', oddsOnly]].forEach(([label, list]) => {
      if (list.length === 0) { return; }
      const ok = list.filter(x => x.correct === true).length;
      let wc=0, dc=0, lc=0;
      for (const m of list) {
        const parts = m.score.split(':');
        if (parts.length === 2) {
          const h = parseInt(parts[0]), a = parseInt(parts[1]);
          if (h > a) wc++; else if (h === a) dc++; else lc++;
        }
      }
      console.log('  ' + label + ': ' + list.length + '场 准=' + ok + '(' + (ok/list.length*100).toFixed(0) + '%) 实际:主胜' + wc + '(' + (wc/list.length*100).toFixed(0) + '%) 平' + dc + '(' + (dc/list.length*100).toFixed(0) + '%) 客胜' + lc + '(' + (lc/list.length*100).toFixed(0) + '%)');
      // 显示最近2场
      list.slice(-2).forEach(x => console.log('    ' + (x.correct?'✅':'❌') + ' ' + x.name + ' ' + x.score + ' 胜赔=' + x.win.toFixed(2)));
    });
    if (strict.length === 0 && rqOpen.length === 0 && oddsOnly.length === 0) {
      console.log('  ⚠️ 无任何匹配');
    }
    console.log();
  }
}
main().catch(e => console.error(e));
