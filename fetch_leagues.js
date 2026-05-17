const https = require('https');
const fs = require('fs');

https.get('https://liansai.500.com/', { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
  const chunks = [];
  res.on('data', c => chunks.push(c));
  res.on('end', () => {
    const buf = Buffer.concat(chunks);
    let html;
    try {
      const iconv = require('iconv-lite');
      html = iconv.decode(buf, 'gb2312');
    } catch(e) {
      html = buf.toString('utf8');
    }
    
    // Extract all league links: /zuqiu-{ID}/ with title
    const regex = /href="https:\/\/liansai\.500\.com\/zuqiu-(\d+)\/"[^>]*target="_blank"[^>]*title="([^"]*)"/g;
    let m;
    const leagues = [];
    const seen = new Set();
    while ((m = regex.exec(html)) !== null) {
      const id = m[1];
      const name = m[2].trim();
      if (!seen.has(id) && name) {
        seen.add(id);
        leagues.push({ id, name });
      }
    }
    
    console.log('Total: ' + leagues.length + ' leagues');
    leagues.slice(0, 30).forEach(l => console.log(l.id + ' | ' + l.name));
    if (leagues.length > 30) console.log('... (' + (leagues.length - 30) + ' more)');
    
    // Save as JSON
    fs.writeFileSync('jingcai/leagues_all.json', JSON.stringify(leagues, null, 2), 'utf8');
    console.log('\nSaved to leagues_all.json');
  });
}).on('error', e => console.error(e.message));
