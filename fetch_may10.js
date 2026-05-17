const https = require('https');
const fs = require('fs');
const apiKey = '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';
const dbId = '35491ad7-17ba-81cc-aa04-ce53f7234e17';

let allResults = [];

function query(cursor) {
  const body = JSON.stringify({ page_size: 100, start_cursor: cursor || undefined });
  const req = https.request({
    hostname: 'api.notion.com',
    path: '/v1/databases/' + dbId + '/query',
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + apiKey,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body)
    }
  }, res => {
    let data = '';
    res.on('data', c => data += c);
    res.on('end', () => {
      const r = JSON.parse(data);
      allResults = allResults.concat(r.results || []);
      if (r.has_more && r.next_cursor) {
        query(r.next_cursor);
      } else {
        const may10 = allResults.filter(p => p.properties['比赛日期']?.date?.start === '2026-05-10');
        console.log('Found', may10.length, 'matches on 2026-05-10');
        
        const results = may10.map(p => {
          const name = p.properties['Name']?.title?.map(t => t.plain_text).join('') || '';
          const jcRaw = p.properties['竞彩预测']?.rich_text?.map(t => t.plain_text).join('') || '';
          const zjRaw = p.properties['步26_庄家最看好']?.rich_text?.map(t => t.plain_text).join('') || '';
          const rqRaw = p.properties['让球预测']?.rich_text?.map(t => t.plain_text).join('') || '';
          const sb = p.properties['实际比分']?.rich_text?.map(t => t.plain_text).join('') || '';
          
          // Extract simple 胜平负 from jingcai
          let jc = '';
          if (jcRaw.includes('主胜')) jc = '主胜';
          else if (jcRaw.includes('平局')) jc = '平局';
          else if (jcRaw.includes('客胜')) jc = '客胜';
          
          // Extract simple 胜平负 from zjzk
          let zj = '';
          if (zjRaw.includes('主胜')) zj = '主胜';
          else if (zjRaw.includes('平局')) zj = '平局';
          else if (zjRaw.includes('客胜')) zj = '客胜';
          
          // Extract rangqiu type
          let rq = '';
          if (rqRaw.includes('让球平')) rq = '让球平';
          else if (rqRaw.includes('让球主胜')) rq = '让球主胜';
          else if (rqRaw.includes('让球客胜')) rq = '让球客胜';
          else if (rqRaw.includes('受让球平')) rq = '受让球平';
          else if (rqRaw.includes('受让主胜')) rq = '受让主胜';
          else if (rqRaw.includes('受让客胜')) rq = '受让客胜';
          
          return { name, jc, zj, rq, sb };
        });
        
        fs.writeFileSync('C:/Users/lianjie/.openclaw/workspace/jingcai/may10_data.json', JSON.stringify(results, null, 2), 'utf8');
        console.log('Wrote', results.length, 'matches to may10_data.json');
        
        // Group by jc+zj+rq
        const groups = {};
        results.forEach(r => {
          const key = `${r.jc} | ${r.zj || '(空)'} | ${r.rq || '(空)'}`;
          if (!groups[key]) groups[key] = [];
          groups[key].push(r);
        });
        
        console.log('\n=== 分组统计 ===');
        Object.keys(groups).sort().forEach(key => {
          const g = groups[key];
          let correct = 0;
          g.forEach(m => {
            if (m.sb) {
              // Determine actual result from score
              const scores = m.sb.split(':').map(s => parseInt(s.trim()));
              if (scores.length === 2) {
                if (scores[0] > scores[1]) {
                  if (m.jc === '主胜') correct++;
                } else if (scores[0] < scores[1]) {
                  if (m.jc === '客胜') correct++;
                } else {
                  if (m.jc === '平局') correct++;
                }
              }
            }
          });
          console.log(`${key}: ${g.length}场, 竞彩正确${correct}场 (${(correct/g.length*100).toFixed(1)}%)`);
          g.forEach(m => console.log(`  ${m.name} | 竞彩:${m.jc} | 庄家:${m.zj||'(空)'} | 让球:${m.rq||'(空)'} | 比分:${m.sb||'(未赛)'}`));
        });
      }
    });
  });
  req.write(body);
  req.end();
}

query();
