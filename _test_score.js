const https = require('https');

const fid = process.argv[2] || '1364061';
const url = 'https://odds.500.com/info.php?fid=' + fid;

https.get(url, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    // Search for score in HTML
    const matches = d.match(/(比分|赛果|score|result)[:=]["'\s]*(\d+[:：]\d+)/i);
    if (matches) {
      console.log('Found score:', matches[2]);
    } else {
      // Try raw patterns
      const scorePattern = />(\d+)\s*[:：]\s*(\d+)</;
      const m = d.match(scorePattern);
      if (m) console.log('Found raw score:', m[1] + ':' + m[2]);
      else console.log('No score found in page');
    }
    console.log('Page length:', d.length);
    // Print around "result" or "score"
    const idx = d.toLowerCase().indexOf('result');
    if (idx >= 0) console.log('Around "result":', d.substring(Math.max(0,idx-50), idx+100));
    const idx2 = d.toLowerCase().indexOf('score');
    if (idx2 >= 0) console.log('Around "score":', d.substring(Math.max(0,idx2-50), idx2+100));
    const idx3 = d.indexOf('赛果');
    if (idx3 >= 0) console.log('Around 赛果:', d.substring(Math.max(0,idx3-50), idx3+100));
    const idx4 = d.indexOf('比分');
    if (idx4 >= 0) console.log('Around 比分:', d.substring(Math.max(0,idx4-50), idx4+100));
    
    // Print all digit:digit patterns
    const allScores = d.match(/(\d+)[:：](\d+)/g);
    if (allScores) console.log('All digit:digit:', [...new Set(allScores)].join(', '));
  });
});
