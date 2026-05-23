// 竞彩数据同步到 Notion 数据库
// 用法:
//   node sync_notion.js add <date>          # 添加比赛
//   node sync_notion.js update <date>       # 更新反馈

const https = require('https');
const fs = require('fs');
const path = require('path');
const log = require('./_log_util.js');
log.setLogDir(path.join(__dirname, 'tasks', new Date().toISOString().slice(0,10), 'logs'));

const NOTION_API_KEY = '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';
const DATABASE_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17';
// 26步+结论数据库
const STEPS_DATABASE_ID = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9';
const STEPS_DB_UPDATED = {};
const JINGCAI_DIR = path.join(__dirname);
const ENV_TASKS_DIR = process.env.NOTION_TASKS_DIR;
const TASKS_DIR = ENV_TASKS_DIR ? path.resolve(ENV_TASKS_DIR) : path.join(JINGCAI_DIR, 'tasks');
if (ENV_TASKS_DIR) { console.log('[INFO] NOTION_TASKS_DIR: ' + TASKS_DIR); }

const headers = {
  'Authorization': 'Bearer ' + NOTION_API_KEY,
  'Notion-Version': '2022-06-28',
  'Content-Type': 'application/json',
};

function notionRequest(method, endpoint, data) {
  return new Promise((resolve, reject) => {
    const body = data ? JSON.stringify(data) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: endpoint,
      method,
      headers: {
        ...headers,
        'Content-Length': Buffer.byteLength(body || ''),
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(d) });
        } catch (e) {
          resolve({ status: res.statusCode, data: d });
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function notionTitleProp(text) {
  return { title: [{ text: { content: String(text) } }] };
}

function notionRichTextProp(text) {
  return text ? { rich_text: [{ text: { content: String(text) } }] } : { rich_text: [] };
}

function notionSelectProp(value) {
  return value ? { select: { name: String(value) } } : { select: null };
}

function notionDateProp(dateStr) {
  return dateStr ? { date: { start: dateStr } } : { date: null };
}

function notionCheckboxProp(value) {
  return { checkbox: Boolean(value) };
}

// ============ 26 steps + final conclusion parser ============
const STEPS_CN = ['十','十一','十二','十三','十四','十五','十六','十七','十八','十九','二十','二十一','二十二','二十三','二十四','二十五','二十六'];

function parseReport26Steps(content) {
  const steps = {};

  // Step 1-8
  for (let i = 1; i <= 8; i++) {
    const h = `## 第${i}步`;
    const nh = i < 8 ? `## 第${i+1}步` : '# 第四部分';
    const si = content.indexOf(h);
    if (si >= 0) {
      const ni = content.indexOf(nh, si + h.length);
      steps[`第${i}步`] = content.substring(si, ni >= 0 ? ni : content.length).trim();
    }
  }

  // Step 9: 第四部分 -> 第十步
  const s9s = content.indexOf('# 第四部分');
  const s10s = content.indexOf('## 第十步');
  if (s9s >= 0 && s10s >= 0) steps['第9步'] = content.substring(s9s, s10s).trim();

  // Step 10-18 (Step 14 has no explicit heading, handled separately)
  for (let i = 10; i <= 18; i++) {
    const idx = i - 10;
    const h = `## 第${STEPS_CN[idx]}步`;
    let nh;
    if (i === 13) {
      nh = '## 第十五步';  // Step 14 has no heading, skip it
    } else if (i < 18) {
      nh = `## 第${STEPS_CN[idx+1]}步`;
    } else {
      nh = '# 第六部分';
    }
    const si = content.indexOf(h);
    if (si >= 0) {
      const ni = content.indexOf(nh, si + h.length);
      steps[`第${i}步`] = content.substring(si, ni >= 0 ? ni : content.length).trim();
    }
  }
  // Step 14 has no explicit heading, use section content
  const s14s = content.indexOf('# 第五部分');
  const s15s = content.indexOf('## 第十五步');
  if (s14s >= 0 && s15s >= 0) steps['第14步'] = content.substring(s14s, s15s).trim();

  // Step 19: 第六部分 -> 第二十步
  const s19s = content.indexOf('# 第六部分');
  const s20s = content.indexOf('## 第二十步');
  if (s19s >= 0 && s20s >= 0) steps['第19步'] = content.substring(s19s, s20s).trim();

  // Step 20-21
  for (let i = 20; i <= 21; i++) {
    const h = `## 第${STEPS_CN[i-10]}步`;
    const nh = i < 21 ? `## 第${STEPS_CN[i-10+1]}步` : '# 第七部分';
    const si = content.indexOf(h);
    if (si >= 0) {
      const ni = content.indexOf(nh, si + h.length);
      steps[`第${i}步`] = content.substring(si, ni >= 0 ? ni : content.length).trim();
    }
  }

  // Step 22: between 21 and 23
  const s21s = content.indexOf('## 第二十一步');
  const s23s = content.indexOf('## 第二十三步');
  if (s21s >= 0 && s23s >= 0) steps['第22步'] = content.substring(s21s, s23s).trim();

  // Step 23
  if (s23s >= 0) {
    const ni = content.indexOf('# 第七部分', s23s);
    steps['第23步'] = content.substring(s23s, ni >= 0 ? ni : content.length).trim();
  }

  // Step 24: 第七部分 -> 第八部分:
  const s24s = content.indexOf('# 第七部分');
  const s25s = content.indexOf('# 第八部分:');
  if (s24s >= 0 && s25s >= 0) steps['第24步'] = content.substring(s24s, s25s).trim();

  // Step 25: 第八部分: 庄家盈亏分析
  const s25h = '# 第八部分: 庄家盈亏分析';
  const s26h = '# 第八部分续: 庄家盈亏占比分析';
  const s25i = content.indexOf(s25h);
  const s26i = content.indexOf(s26h);
  if (s25i >= 0 && s26i >= 0) steps['第25步'] = content.substring(s25i, s26i).trim();

  // Step 26
  const s27s = content.indexOf('# 第九部分');
  if (s26i >= 0 && s27s >= 0) steps['第26步'] = content.substring(s26i, s27s).trim();

  // Final conclusion
  if (s27s >= 0) {
    let c = content.substring(s27s).trim();
    c = c.replace(/\n---+[\s\S]*$/, '');
    steps['最终结论'] = c;
  }

  return steps;
}

// Truncate step text for Notion (keep summary + last 500 chars)
function truncateStep(text, maxLen) {
  maxLen = maxLen || 800;
  if (!text) return '';
  if (text.length <= maxLen) return text;
  // Keep first maxLen-30 chars, then indicate truncation
  return text.substring(0, maxLen - 30) + '\n...(已截断)';
}

function notionRichTextPropChunked(text) {
  if (!text) return { rich_text: [] };
  const chunks = [];
  const max = 1900;
  for (let i = 0; i < text.length; i += max) {
    chunks.push({ text: { content: text.substring(i, i + max) } });
  }
  return { rich_text: chunks };
}

/**
 * Sync report to 26-steps database (历史每日报告汇总)
 * Database ID: STEPS_DATABASE_ID
 * Only one property "比赛" (title), 26 step columns + 最终结论 are rich_text
 */
async function syncToStepsDB(reportPath) {
  const content = fs.readFileSync(reportPath, 'utf8');
  const steps = parseReport26Steps(content);

  // Extract meta from report
  const fn = path.basename(reportPath);
  const tm = fn.match(/周([^"]+)"_"(.+?)vs(.+)/);
  let title = fn.replace('.md', '');

  // Build properties: "比赛" is title, plus 26 step columns + final conclusion
  const properties = {
    '比赛': notionTitleProp(title),
  };

  for (let i = 1; i <= 26; i++) {
    const label = `第${i}步`;
    const text = steps[label] || '';
    properties[label] = notionRichTextPropChunked(truncateStep(text, 1000));
  }
  properties['最终结论'] = notionRichTextPropChunked(steps['最终结论'] || '');

  const res = await notionRequest('POST', '/v1/pages', {
    parent: { database_id: STEPS_DATABASE_ID },
    properties,
  });

  if (res.status === 200) {
    console.log(`[STEPS OK] ${title} -> 26步数据库 page=${res.data.id}`);
    return res.data.id;
  } else {
    console.error(`[STEPS ERR] ${title}: ${res.status} ${JSON.stringify(res.data).substring(0, 200)}`);
    return null;
  }
}

function extractMatchInfo(reportPath, matchDir, metaData) {
  const content = fs.readFileSync(reportPath, 'utf8');
  const fn = path.basename(reportPath);

  // 提取日期前缀(周X)
  const dayMatch = fn.match(/周([一二三四五六日])/);
  const dayMap = {'一':'一','二':'二','三':'三','四':'四','五':'五','六':'六','日':'日'};
  const dayPrefix = dayMatch ? '周' + dayMap[dayMatch[1]] : '';

  // 提取竞彩编号
  const mn = fn.match(/周[一二三四五六日](\d{3})/);
  const matchNum = mn ? mn[1] : '';

  // 提取对阵
  const tm = fn.match(/周[一二三四五六日]\d{3}_(.+?)vs(.+?)\.md/);
  const home = tm ? tm[1].trim() : '';
  const away = tm ? tm[2].trim() : '';

  // 提取联赛
  let league = '';
  const lm = content.match(/比赛[::]\s*([^·\n]+)·/);
  if (lm) league = lm[1].trim();

  // 提取最终结论部分(第九部分)
  const conclusionSection = content.match(/# 第九[\s\S]*?(?=# [^九]|$)/);
  const conclusionText = conclusionSection ? conclusionSection[0] : '';

  // 从报告全文提取各指标评分(在"各维度信号明细"表中)
  // 格式:| 欧赔趋势 | +0.700 利好主 | 10% |
  // 注意: 澳门亚盘需要从结论部分的汇总表提取(趋势格式), 不要匹配到其他位置的水值行
  function extractScoreFromTable(text, label) {
    if (label === '澳门亚盘') {
      // 从全文匹配澳门亚盘趋势行（优先匹配带评分格式的行）
      // 格式: | 澳门亚盘 | +0.083 利好主 | 11% |
      // 或: | 澳门亚盘 | +0.000 中立 | 11% |
      const trendM = text.match(/\|\s*澳门亚盘\s*\|\s*([+-][\d.]+\s+[^|]+)\s*\|\s*([\d.]+%)\s*\|/);
      if (trendM) {
        return trendM[1].trim() + ' | ' + trendM[2].trim();
      }
      return '';
    }
    // Match table row: | 欧赔趋势 | +0.700 利好主 | 10% |
    const m = text.match(new RegExp('\\|\\s*' + label + '\\s*\\|\\s*([^|]+)\\|\\s*([^|]+)\\|'));
    if (m) {
      return m[1].trim() + ' | ' + m[2].trim();
    }
    return '';
  }

  // 从中间数据文件提取(报告汇总表为空时的fallback)
  function extractFromDataFiles() {
    const result = {};
    if (!matchDir || !fs.existsSync(matchDir)) return result;

    // === 提取即时盘赔率数据 ===
    let g1Dir = path.join(matchDir, 'group01_europe');
    if (fs.existsSync(g1Dir)) {
      const s1_md = path.join(g1Dir, 'step01_europe_basic.md');
      const s1_txt = path.join(g1Dir, 'step1_europe_base.txt');
      const s1 = fs.existsSync(s1_md) ? s1_md : (fs.existsSync(s1_txt) ? s1_txt : null);
      if (s1) {
        const c1 = fs.readFileSync(s1, 'utf8');
        const lines1 = c1.split('\n');
        for (const line of lines1) {
          if (!line.includes('|')) continue;
          const parts = line.split('|').map(p => p.trim()).filter(p => p);
          if (parts.length < 8) continue;
          // | 公司 | 初胜 | 初平 | 初负 | 即胜 | 即平 | 即负 | 变化 |
          if (parts[0] === '竞彩官方' && parts[1] !== '-1') {
            result.jc_live_win = Math.floor(parseFloat(parts[4]) * 10) / 10;
            result.jc_live_draw = Math.floor(parseFloat(parts[5]) * 10) / 10;
            result.jc_live_loss = Math.floor(parseFloat(parts[6]) * 10) / 10;
          }
          if (parts[0] === 'Interwetten') {
            result.iw_live_win = Math.floor(parseFloat(parts[4]) * 10) / 10;
            result.iw_live_draw = Math.floor(parseFloat(parts[5]) * 10) / 10;
            result.iw_live_loss = Math.floor(parseFloat(parts[6]) * 10) / 10;
          }
          if (parts[0] === '百家平均') {
            result.bj_live_win = Math.floor(parseFloat(parts[4]) * 10) / 10;
            result.bj_live_draw = Math.floor(parseFloat(parts[5]) * 10) / 10;
            result.bj_live_loss = Math.floor(parseFloat(parts[6]) * 10) / 10;
          }
        }
      }
    }

    // 让球指数（初盘+即时值）
    const g2Dir = path.join(matchDir, 'group02_handicap');
    if (fs.existsSync(g2Dir)) {
      const s4_md = path.join(g2Dir, 'step04_handicap_basic.md');
      const s4_txt = path.join(g2Dir, 'step4_handicap_base.txt');
      const s4 = fs.existsSync(s4_md) ? s4_md : (fs.existsSync(s4_txt) ? s4_txt : null);
      if (s4) {
        const c4 = fs.readFileSync(s4, 'utf8');
        const lines4 = c4.split('\n');
        for (const line of lines4) {
          if (!line.includes('|')) continue;
          const parts = line.split('|').map(p => p.trim()).filter(p => p);
          if (parts.length < 8) continue;
          // | 竞彩官方 | 让球 | 初胜 | 初平 | 初负 | 即胜 | 即平 | 即负 |
          if (parts[0] === '竞彩官方') {
            // 初盘（让球指数）
            result.rq_win = Math.floor(parseFloat(parts[2]) * 10) / 10;
            result.rq_draw = Math.floor(parseFloat(parts[3]) * 10) / 10;
            result.rq_loss = Math.floor(parseFloat(parts[4]) * 10) / 10;
            // 即时盘（终盘让球指数）
            result.rq_live_win = Math.floor(parseFloat(parts[5]) * 10) / 10;
            result.rq_live_draw = Math.floor(parseFloat(parts[6]) * 10) / 10;
            result.rq_live_loss = Math.floor(parseFloat(parts[7]) * 10) / 10;
          }
        }
      }
    }

    // 澳门亚盘（即时值）
    // 优先从meta.json读取macau_line（准确），fallback到step6解析
    const g3Dir = path.join(matchDir, 'group03_asian');
    const metaFile = path.join(matchDir, 'meta.json');
    if (fs.existsSync(metaFile)) {
      try {
        const meta = JSON.parse(fs.readFileSync(metaFile, 'utf8'));
        if (meta.macau_line) {
          result.macau_live = meta.macau_line;
        }
      } catch (e) {}
    }
    // fallback: 从step6提取（兼容旧数据）
    if (!result.macau_live && fs.existsSync(g3Dir)) {
      const s6_md = path.join(g3Dir, 'step06_asian_basic.md');
      const s6_txt = path.join(g3Dir, 'step6_asian_base.txt');
      const s6 = fs.existsSync(s6_md) ? s6_md : (fs.existsSync(s6_txt) ? s6_txt : null);
      if (s6) {
        const c6 = fs.readFileSync(s6, 'utf8');
        const lines6 = c6.split('\n');
        for (const line of lines6) {
          if (!line.includes('澳门')) continue;
          const parts = line.split('|').map(p => p.trim()).filter(p => p);
          if (parts.length >= 3) {
            const liveText = parts[2] || '';
            const clean = liveText.replace(/\d+\.\d+\|\d+\.\d+/, '').replace(/[⬆⬇➡⬆⬇]/g, '').trim();
            result.macau_live = clean;
          }
          break;
        }
      }
    }

    // 读取group01_europe下的文件
    // g1Dir already declared above
    if (fs.existsSync(g1Dir)) {
      // step1_europe_base.txt - 欧赔基础
      const s1_md = path.join(g1Dir, 'step01_europe_basic.md');
      const s1_txt = path.join(g1Dir, 'step1_europe_base.txt');
      const s1 = fs.existsSync(s1_md) ? s1_md : (fs.existsSync(s1_txt) ? s1_txt : null);
      if (s1) {
        const c1 = fs.readFileSync(s1, 'utf8');
        // 提取竞彩官方赔率变化
        const scm = c1.match(/竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([^|]+)/);
        if (scm) {
          const changes = scm[7].trim();
          const initOdds = `${scm[1]}/${scm[2]}/${scm[3]}`;
          const liveOdds = `${scm[4]}/${scm[5]}/${scm[6]}`;
          result.jc_panlu = `${changes}`;
        }
        // Interwetten赔率变化
        const iwm = c1.match(/Interwetten\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([^|]+)/);
        if (iwm) {
          result.iw_panlu = `${iwm[7].trim()}`;
        }
        // 百家平均赔率变化
        const bjm = c1.match(/百家平均\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([^|]+)/);
        if (bjm) {
          result.bj_panlu = `${bjm[7].trim()}`;
        }
      }
      // step2_jingcai_same.txt - 竞彩同赔
      const s2_md = path.join(g1Dir, 'step02_jingcai_same.md');
      const s2_txt = path.join(g1Dir, 'step2_jingcai_same.txt');
      const s2 = fs.existsSync(s2_md) ? s2_md : (fs.existsSync(s2_txt) ? s2_txt : null);
      if (s2) {
        const c2 = fs.readFileSync(s2, 'utf8');
        const countMatch = c2.match(/共(\d+)\s*场/);
        const winMatch = c2.match(/胜(\d+)\s*平(\d+)\s*负(\d+)/);
        if (countMatch) {
          result.jingcai_same_count = `${countMatch[1]}场`;
          if (winMatch) {
            result.jingcai_same = `${countMatch[1]}场:胜${winMatch[1]}(${winMatch[1]===0?0:Math.round(winMatch[1]/countMatch[1]*100)}%) 平${winMatch[2]}(${winMatch[2]===0?0:Math.round(winMatch[2]/countMatch[1]*100)}%) 负${winMatch[3]}(${winMatch[3]===0?0:Math.round(winMatch[3]/countMatch[1]*100)}%)`;
          } else {
            result.jingcai_same = `${countMatch[1]}场`;
          }
        }
      }
      // step3_interwetten_same.txt - IW同赔
      const s3_md = path.join(g1Dir, 'step03_interwetten_same.md');
      const s3_txt = path.join(g1Dir, 'step3_interwetten_same.txt');
      const s3 = fs.existsSync(s3_md) ? s3_md : (fs.existsSync(s3_txt) ? s3_txt : null);
      if (s3) {
        const c3 = fs.readFileSync(s3, 'utf8');
        const iwCountMatch = c3.match(/共(\d+)\s*场/);
        const iwWinMatch = c3.match(/胜(\d+)\s*平(\d+)\s*负(\d+)/);
        if (iwCountMatch) {
          result.iw_same_count = `${iwCountMatch[1]}场`;
          if (iwWinMatch) {
            result.iw_same = `${iwCountMatch[1]}场:胜${iwWinMatch[1]}(${iwWinMatch[1]===0?0:Math.round(iwWinMatch[1]/iwCountMatch[1]*100)}%) 平${iwWinMatch[2]}(${iwWinMatch[2]===0?0:Math.round(iwWinMatch[2]/iwCountMatch[1]*100)}%) 负${iwWinMatch[3]}(${iwWinMatch[3]===0?0:Math.round(iwWinMatch[3]/iwCountMatch[1]*100)}%)`;
          } else {
            result.iw_same = `${iwCountMatch[1]}场`;
          }
        }
      }
    }

    // 读取group02_handicap下的文件
    // g2Dir already declared above
    if (fs.existsSync(g2Dir)) {
      // 让球指数盘路(从step04提取)
      const rqMd = path.join(g2Dir, 'step04_handicap_basic.md');
      const rqTxt = path.join(g2Dir, 'step4_handicap_base.txt');
      const rqFile = fs.existsSync(rqMd) ? rqMd : (fs.existsSync(rqTxt) ? rqTxt : null);
      if (rqFile) {
        const c4panlu = fs.readFileSync(rqFile, 'utf8');
        const rqm2 = c4panlu.match(/竞彩官方\s*\|\s*[^|]+\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/);
        if (rqm2) {
          const rq_dir = [(rqm2[4]>rqm2[1]?'⬆':rqm2[4]<rqm2[1]?'⬇':'➡'),(rqm2[5]>rqm2[2]?'⬆':rqm2[5]<rqm2[2]?'⬇':'➡'),(rqm2[6]>rqm2[3]?'⬆':rqm2[6]<rqm2[3]?'⬇':'➡')]; result.rq_panlu = rq_dir.join('');
        }
      }
      // step5_handicap_same.txt - 让球同赔
      const s5_md = path.join(g2Dir, 'step05_handicap_same.md');
      const s5_txt = path.join(g2Dir, 'step5_handicap_same.txt');
      const s5 = fs.existsSync(s5_md) ? s5_md : (fs.existsSync(s5_txt) ? s5_txt : null);
      if (s5) {
        const c5 = fs.readFileSync(s5, 'utf8');
        const hCountMatch = c5.match(/共(\d+)\s*场/);
        if (hCountMatch) {
          result.handicap_same_count = `${hCountMatch[1]}场`;
        }
      }
    }

    // 读取group03_asian下的文件
    // g3Dir already declared above
    if (fs.existsSync(g3Dir)) {
      // step6_asian_base.txt - 亚盘基础（不写macau_asian，报告里已有趋势格式）
      // step7_macau_same.txt - 澳门亚盘同赔
      const s7_md = path.join(g3Dir, 'step07_macau_same.md');
      const s7_txt = path.join(g3Dir, 'step7_macau_same.txt');
      const s7 = fs.existsSync(s7_md) ? s7_md : (fs.existsSync(s7_txt) ? s7_txt : null);
      if (s7) {
        const c7 = fs.readFileSync(s7, 'utf8');
        const mCountMatch = c7.match(/共\s*(\d+)\s*场/);
        if (mCountMatch) {
          result.macau_same_count = `${mCountMatch[1]}场`;
        }
      }
      // 澳门亚盘盘路(从step06提取)
      // 格式: "半球 → 半球" (初盘盘口 → 即时盘盘口)
      const macauMd = path.join(g3Dir, 'step06_asian_basic.md');
      const macauTxt = path.join(g3Dir, 'step6_asian_base.txt');
      const macauFile = fs.existsSync(macauMd) ? macauMd : (fs.existsSync(macauTxt) ? macauTxt : null);
      if (macauFile) {
        const c6panlu = fs.readFileSync(macauFile, 'utf8');
        for (const line of c6panlu.split('\n')) {
          if (!line.includes('澳门')) continue;
          // 用 | 周边有空格的方式分割列，避免水位值内部的 | 被误切
          // 格式: | 澳门 | 平手/半球 0.960|0.880 | 平手/半球 0.900|0.940 |
          // 新格式: | 澳门 | 半球 降（主水0.840|客水1.000） | 半球/一球（主水0.890|客水0.950） |
          const lineClean = line.replace(/^\|\s*|\s*\|$/g, '').trim();
          const parts = lineClean.split(/\s+\|\s+/);
          if (parts.length >= 3) {
            // 提取初盘盘口(去掉"降""升"等标记和水位)
            const initRaw = (parts[1] || '').split(/\s+/)[0];
            const liveRaw = (parts[2] || '').split(/\s+/)[0];
            result.macau_panlu = initRaw + ' → ' + liveRaw;
          }
          break;
        }
      }
      // step8_same_league.txt - 同联赛亚盘统计
      const s8_md = path.join(g3Dir, 'step08_same_league.md');
      const s8_txt = path.join(g3Dir, 'step8_same_league.txt');
      const s8 = fs.existsSync(s8_md) ? s8_md : (fs.existsSync(s8_txt) ? s8_txt : null);
      if (s8) {
        const c8 = fs.readFileSync(s8, 'utf8');
        const totalMatch = c8.match(/总场次:\s*(\d+)/);
        const winRateMatch = c8.match(/主场胜率:\s*([\d.]+)%/);
        if (totalMatch) {
          result.same_league_count = `${totalMatch[1]}场`;
          if (winRateMatch) {
            result.same_league_winrate = `${winRateMatch[1]}%`;
          }
        }
      }
    }

    // 读取group04_teamA下的文件
    const g4Dir = path.join(matchDir, 'group04_teamA');
    if (fs.existsSync(g4Dir)) {
      const s9_md = path.join(g4Dir, 'step09_13_teamA.md');
      const s9_txt = path.join(g4Dir, 'step9_home_history.txt');
      const s9 = fs.existsSync(s9_md) ? s9_md : (fs.existsSync(s9_txt) ? s9_txt : null);
      if (s9) {
        const c9 = fs.readFileSync(s9, 'utf8');
        const homeCountMatch = c9.match(/共(\d+)场/);
        const homeWinMatch = c9.match(/胜率([\d.]+)%/);
        if (homeCountMatch) {
          result.home_count = `${homeCountMatch[1]}场`;
          if (homeWinMatch) {
            result.home_winrate = `${homeWinMatch[1]}%`;
          }
        }
      }
    }

    // 读取group05_teamB下的文件
    const g5Dir = path.join(matchDir, 'group05_teamB');
    if (fs.existsSync(g5Dir)) {
      const s14_md = path.join(g5Dir, 'step14_18_teamB.md');
      const s14_txt = path.join(g5Dir, 'step14_away_history.txt');
      const s14 = fs.existsSync(s14_md) ? s14_md : (fs.existsSync(s14_txt) ? s14_txt : null);
      if (s14) {
        const c14 = fs.readFileSync(s14, 'utf8');
        const awayCountMatch = c14.match(/共(\d+)场/);
        const awayWinMatch = c14.match(/胜率([\d.]+)%/);
        if (awayCountMatch) {
          result.away_count = `${awayCountMatch[1]}场`;
          if (awayWinMatch) {
            result.away_winrate = `${awayWinMatch[1]}%`;
          }
        }
      }
    }

    // 读取group06_baijia下的文件
    const g6Dir = path.join(matchDir, 'group06_baijia');
    if (fs.existsSync(g6Dir)) {
      const s19 = path.join(g6Dir, 'step19_baijia_compare.txt');
      if (fs.existsSync(s19)) {
        const c19 = fs.readFileSync(s19, 'utf8');
        const bjCountMatch = c19.match(/共(\d+)场/);
        if (bjCountMatch) {
          result.baijia_count = `${bjCountMatch[1]}场`;
        }
      }
    }

    return result;
  }

  // 先从报告提取,再从中间数据文件fallback
  let oupei_trend = extractScoreFromTable(content, '欧赔趋势');
  let iw_tongpei = extractScoreFromTable(content, 'IW同赔');
  let macau_asian = extractScoreFromTable(content, '澳门亚盘');
  let home_home = extractScoreFromTable(content, '主队主场');
  let away_away = extractScoreFromTable(content, '客队客场');
  let baijia = extractScoreFromTable(content, '百家对比');
  let oupei_combo = extractScoreFromTable(content, '欧赔组合');

  // 如果报告里没有汇总表,从中间数据文件提取
  const dataFiles = extractFromDataFiles();
  if (!oupei_trend && dataFiles.oupei_base) oupei_trend = dataFiles.oupei_base;
  if (!iw_tongpei && dataFiles.iw_same) iw_tongpei = dataFiles.iw_same;
  if (!macau_asian && dataFiles.macau_asian) macau_asian = dataFiles.macau_asian;
  if (!home_home && dataFiles.home_count) home_home = `历史${dataFiles.home_count}${dataFiles.home_winrate?` 胜率${dataFiles.home_winrate}`:''}`;
  if (!away_away && dataFiles.away_count) away_away = `历史${dataFiles.away_count}${dataFiles.away_winrate?` 胜率${dataFiles.away_winrate}`:''}`;
  if (!baijia && dataFiles.baijia_count) baijia = `对比${dataFiles.baijia_count}`;
  if (!oupei_combo && dataFiles.jingcai_same) oupei_combo = `竞彩同赔${dataFiles.jingcai_same}`;

  // 风险提示(从 ### 风险提示 提取)
  let risk = '';
  const riskMarker = '\u98ce\u9669\u63d0\u793a';
  const riskIdx = content.indexOf(riskMarker);
  if (riskIdx >= 0) {
    // Find the start of the section (after the newline following "风险提示")
    const sectionStart = content.indexOf('\n', riskIdx) + 1;
    // Find the end (next ### section or ---)
    const nextSection = content.indexOf('\n### ', sectionStart);
    const sectionEnd = nextSection >= 0 ? nextSection : content.length;
    const sectionText = content.substring(sectionStart, sectionEnd);

    const bullets = sectionText.match(/- ([^\r\n]+)/g);
    if (bullets) {
      risk = bullets.map(b => b.replace(/^- /, '').trim()).join(';');
    }
  }

  // 竞彩预测(从最终结论提取)
  let pred = '';
  const pm = conclusionText.match(/竞彩预测[::]\s*([^\n|]+)/);
  if (pm) pred = pm[1].trim();
  if (!pred) {
    // 新版表格格式: | **竞彩预测** | 主胜（信心67% 中信号） |
    const pm2 = content.match(/\|\s*\*\*竞彩预测\*\*\s*\|\s*([^|]+)\s*\|/);
    if (pm2) pred = pm2[1].trim();
  }
  if (!pred) {
    // 兼容旧版: **推荐** | 主胜
    const rec = content.match(/\*\*推荐\*\*\s*\|\s*([^\|]+)/);
    if (rec) pred = rec[1].trim();
  }

  // 让球预测(从最终结论提取)
  let rq_pred = '';
  let rq_pred_full = '';
  const rqm = conclusionText.match(/让球预测[::]\s*([^\n|]+)/);
  if (rqm) rq_pred_full = rqm[1].trim();
  if (!rq_pred_full) {
    // 新版表格格式: | **让球预测** | 让2球 让球客胜（数据不足，仅供参考）（信心55%） |
    const rq2 = content.match(/\|\s*\*\*让球预测\*\*\s*\|\s*([^|]+)\s*\|/);
    if (rq2) rq_pred_full = rq2[1].trim();
  }
  // 提取核心方向、让球数和信心，去掉中间备注文本
  // 格式: "让1球 让球客胜（信心不足...）（信心0%）" → "让1球 让球客胜（0%）"
  const rqCore = rq_pred_full.match(/(让球主胜|让球客胜|让球平)/);
  const rqPrefix = rq_pred_full.match(/^((?:让\d+(?:\.5)?球|受让\d+(?:\.5)?球|平手)\s*)/);
  const rqConf = rq_pred_full.match(/（信心(\d+)%）/);
  let rqDirection = rqCore ? rqCore[1] : '';
  let rqHandicapText = rqPrefix ? rqPrefix[1].trim() : '';
  let rqConfText = rqConf ? '（' + rqConf[1] + '%）' : '';
  if (rqHandicapText && rqDirection) {
    rq_pred = rqHandicapText + ' ' + rqDirection + rqConfText;
  } else if (rqDirection) {
    rq_pred = rqDirection + rqConfText;
  } else {
    rq_pred = rq_pred_full;
  }

  // 让球数(从第4步让球指数明细提取)
  // 格式:| 竞彩官方 | -1 | 2.60 | 3.45 | 2.20 | 2.05 | 3.53 | 2.79 |
  // 注意:报告里带-号的是主队让球,不带-的是主队受让球
  // 需要取反:-1 → 1(让球),1 → -1(受让)
  let handicap = 0;
  const rqTable = content.match(/\|\s*竞彩官方\s*\|\s*([+-]?\d+(?:\.5)?)\s*\|/);
  if (rqTable) {
    handicap = -parseFloat(rqTable[1]);  // 取反
  }

  // 读取step25/step26数据（从match目录）
  let s25_zjyk = '';
  let s26_zzhk = '';
  let s26_zjyf = '';
  let s26_ykbz = '';
  let s26_tzbz = '';
  
  // 提取澳门亚盘即时盘口（从step6提取即时盘）
  let macau_asian_instant = '';
  if (matchDir && fs.existsSync(matchDir)) {
    const step6Path = path.join(matchDir, 'group03_asian', 'step06_asian_basic.md');
    if (fs.existsSync(step6Path)) {
      const c6 = fs.readFileSync(step6Path, 'utf8');
      const lines6 = c6.split('\n');
      for (const line of lines6) {
        if (!line.includes('澳门')) continue;
        const parts = line.split('|').map(p => p.trim()).filter(p => p);
        if (parts.length >= 3) {
          // 澳门亚盘格式：| 澳门 | 初盘(盘口 水位|水位) | 即时盘(盘口 水位|水位) |
          // 提取即时盘口的盘口部分（去掉水位）
          const liveText = parts[parts.length - 1] || '';
          // 盘口格式：半球 0.840|1.000 或 平手/半球 0.840|1.000
          const panMatch = liveText.match(/^[^\s]+/);
          if (panMatch) {
            macau_asian_instant = panMatch[0].trim();
          } else {
            macau_asian_instant = liveText.replace(/\s+\d+\.\d+\|\d+\.\d+/, '').trim();
          }
        }
        break;
      }
    }
  }
  
  // 庄家数据:优先从matchDir读取,备选从JINGCAI_DIR/tasks/DATE/data/读取
  function readStep25Data(baseDir) {
    const s25Path = path.join(baseDir, 'step25_zhuangjia.json');
    if (!fs.existsSync(s25Path)) return null;
    try {
      const s25 = JSON.parse(fs.readFileSync(s25Path, 'utf8'));
      const labels = s25.labels || {};
      const parts = [];
      for (const cat of ['主胜', '平局', '客胜']) {
        if (labels[cat]) {
          const l = labels[cat];
          parts.push(`${cat}:${l.bet_pct || '-'}/成交${l.volume || '-'}/庄家${l.profit || '-'}`);
        }
      }
      if (parts.length > 0) return parts.join(' | ');
    } catch(e) {}
    return null;
  }
  if (matchDir && fs.existsSync(matchDir)) {
    s25_zjyk = readStep25Data(matchDir) || '';
    // 备选:从JINGCAI_DIR/tasks/DATE/data读取
    // 备选:从JINGCAI_DIR/tasks/DATE/data读取(仅当比赛编号匹配)
    if (!s25_zjyk && metaData && metaData.matchnum) {
      const dateMatch = matchDir.match(/(\d{4}-\d{2}-\d{2})/);
      if (dateMatch) {
        const altDir = path.join(JINGCAI_DIR, 'tasks', dateMatch[1], 'data');
        if (fs.existsSync(altDir)) {
          try {
            const fp = path.join(altDir, 'step25_zhuangjia.json');
            if (fs.existsSync(fp)) {
              const tmp = JSON.parse(fs.readFileSync(fp, 'utf8'));
              if (tmp.match_num === metaData.matchnum) {
                s25_zjyk = readStep25Data(altDir);
              }
            }
          } catch(e) {}
        }
      }
    }
  }
  // Step26: 盈亏占比分析(备注:当前pipeline未生成此文件,保留占位)
  if (matchDir) {
    try {
      const s26Path = path.join(matchDir, 'step26_profit_ratio.json');
      if (!fs.existsSync(s26Path)) {
        const dateMatch = matchDir.match(/(\d{4}-\d{2}-\d{2})/);
        if (dateMatch) {
          const altDir = path.join(JINGCAI_DIR, 'tasks', dateMatch[1], 'data');
          const altPath = path.join(altDir, 'step26_profit_ratio.json');
          if (fs.existsSync(altPath)) {
            const s26 = JSON.parse(fs.readFileSync(altPath, 'utf8'));
            const analysis = s26.analysis || {};
            s26_zzhk = analysis['庄家最看好'] || '';
            const dirs = [];
            if (analysis['庄家胜盈亏']) dirs.push('胜:' + analysis['庄家胜盈亏']);
            if (analysis['庄家平盈亏']) dirs.push('平:' + analysis['庄家平盈亏']);
            if (analysis['庄家负盈亏']) dirs.push('负:' + analysis['庄家负盈亏']);
            if (dirs.length > 0) s26_zjyf = dirs.join(' | ');
            const pr = analysis['盈亏占比'] || {};
            const pr_parts = [];
            if (pr['胜'] !== undefined) pr_parts.push('胜:' + (pr['胜']*100).toFixed(1) + '%');
            if (pr['平'] !== undefined) pr_parts.push('平:' + (pr['平']*100).toFixed(1) + '%');
            if (pr['负'] !== undefined) pr_parts.push('负:' + (pr['负']*100).toFixed(1) + '%');
            if (pr_parts.length > 0) s26_ykbz = pr_parts.join(' | ');
            const bp = analysis['投注占比'] || {};
            const bp_parts = [];
            if (bp['胜']) bp_parts.push('胜:' + bp['胜'] + '%');
            if (bp['平']) bp_parts.push('平:' + bp['平'] + '%');
            if (bp['负']) bp_parts.push('负:' + bp['负'] + '%');
            if (bp_parts.length > 0) s26_tzbz = bp_parts.join(' | ');
          }
        }
      } else {
        const s26 = JSON.parse(fs.readFileSync(s26Path, 'utf8'));
        const analysis = s26.analysis || {};
        s26_zzhk = analysis['庄家最看好'] || '';
        const dirs = [];
        if (analysis['庄家胜盈亏']) dirs.push('胜:' + analysis['庄家胜盈亏']);
        if (analysis['庄家平盈亏']) dirs.push('平:' + analysis['庄家平盈亏']);
        if (analysis['庄家负盈亏']) dirs.push('负:' + analysis['庄家负盈亏']);
        if (dirs.length > 0) s26_zjyf = dirs.join(' | ');
        const pr = analysis['盈亏占比'] || {};
        const pr_parts = [];
        if (pr['胜'] !== undefined) pr_parts.push('胜:' + (pr['胜']*100).toFixed(1) + '%');
        if (pr['平'] !== undefined) pr_parts.push('平:' + (pr['平']*100).toFixed(1) + '%');
        if (pr['负'] !== undefined) pr_parts.push('负:' + (pr['负']*100).toFixed(1) + '%');
        if (pr_parts.length > 0) s26_ykbz = pr_parts.join(' | ');
        const bp = analysis['投注占比'] || {};
        const bp_parts = [];
        if (bp['胜']) bp_parts.push('胜:' + bp['胜'] + '%');
        if (bp['平']) bp_parts.push('平:' + bp['平'] + '%');
        if (bp['负']) bp_parts.push('负:' + bp['负'] + '%');
        if (bp_parts.length > 0) s26_tzbz = bp_parts.join(' | ');
      }
    } catch(e) {}
  }

  // 构建比赛显示:周六011 德甲 拜仁vs海登海姆
  const matchDisplay = `${dayPrefix}${matchNum} ${league} ${home}vs${away}`;

  return {
    matchDisplay,
    matchNum,
    league,
    fid: (metaData && metaData.fid) || '',
    oupei_trend,
    iw_tongpei,
    macau_asian,
    home_home,
    away_away,
    baijia,
    oupei_combo,
    risk,
    pred,
    rq_pred,
    handicap,
    oupei_jingcai_panlu: dataFiles.jc_panlu || '',
    oupei_iw_panlu: dataFiles.iw_panlu || '',
    oupei_baijia_panlu: dataFiles.bj_panlu || '',
    macau_panlu: dataFiles.macau_panlu || '',
    rq_panlu: dataFiles.rq_panlu || '',
    s25_zjyk,
    s26_zzhk,
    s26_zjyf,
    s26_ykbz,
    s26_tzbz,
    // 即时盘赔率（即时值，从step文件提取）
    jc_live_win: dataFiles.jc_live_win || 0,
    jc_live_draw: dataFiles.jc_live_draw || 0,
    jc_live_loss: dataFiles.jc_live_loss || 0,
    iw_live_win: dataFiles.iw_live_win || 0,
    iw_live_draw: dataFiles.iw_live_draw || 0,
    iw_live_loss: dataFiles.iw_live_loss || 0,
    bj_live_win: dataFiles.bj_live_win || 0,
    bj_live_draw: dataFiles.bj_live_draw || 0,
    bj_live_loss: dataFiles.bj_live_loss || 0,
    rq_live_win: dataFiles.rq_live_win || 0,
    rq_live_draw: dataFiles.rq_live_draw || 0,
    rq_live_loss: dataFiles.rq_live_loss || 0,
    // 初盘让球指数
    rq_win: dataFiles.rq_win || 0,
    rq_draw: dataFiles.rq_draw || 0,
    rq_loss: dataFiles.rq_loss || 0,
    macau_asian_live: macau_asian_instant || '',
    // 澳门亚盘（从meta.json读取，正确值如"半球"）
    macau_live: dataFiles.macau_live || '',
  };
}

/**
 * 从500.com欧赔页面提取比赛时间（含时分）
 * 返回格式: "2026-05-17T14:00:00+08:00" 或 null
 */
function getMatchTime(fid) {
  if (!fid) return null;
  try {
    const url = 'https://odds.500.com/fenxi/ouzhi-' + fid + '.shtml';
    const cp = require('child_process');
    const data = cp.execSync('curl -s "' + url + '" --max-time 8', { encoding: 'utf8', timeout: 10000 });
    const m = data.match(/class="game_time">\s*比赛时间\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})/);
    if (m) {
      return m[1].replace(' ', 'T') + ':00+08:00';
    }
  } catch(e) {}
  return null;
}

function predictToResult(pred) {
  if (!pred) return '';
  if (pred.includes('主胜') || pred.includes('胜')) return '胜';
  if (pred.includes('客胜') || pred.includes('负')) return '负';
  if (pred.includes('平')) return '平';
  return '';
}

// 从让球预测中提取让球数(如"让-1球"、"受让1球")
function extractHandicap(rq_pred) {
  if (!rq_pred) return 0;
  // 匹配:让-1球、让+1球、让1球、受让1球、让平、让半球等
  const m1 = rq_pred.match(/(?:让|受让)([+-]?\d+(?:\.5)?)/);
  if (m1) {
    let val = parseFloat(m1[1]);
    // 如果是"受让",取负值
    if (rq_pred.includes('受让')) val = -Math.abs(val);
    return val;
  }
  // 匹配:让平
  if (rq_pred.includes('让平') || rq_pred.includes('平手')) return 0;
  return 0;
}

// 根据比分和让球数计算让球后的结果
function calcHandicapResult(home_score, away_score, handicap) {
  // handicap > 0: 主队让球(主队得分 - handicap)
  // handicap < 0: 主队受让(主队得分 + |handicap|)
  const adj_home = home_score - handicap;
  if (adj_home > away_score) return '胜';
  if (adj_home < away_score) return '负';
  return '平';
}

// 判断竞彩预测是否正确
function checkCorrect(pred, actual) {
  if (!pred || !actual || actual === '待查') return null;
  return predictToResult(pred) === actual;
}

// 判断让球预测是否正确
function checkRqCorrect(rq_pred, actual, handicap) {
  if (!rq_pred || rq_pred.includes('待查')) return null;
  const rq_result = predictToResult(rq_pred);
  // 如果让球预测是"让球平",实际让球后结果也应该是平
  if (rq_result === '平') return actual === '平';
  return rq_result === actual;
}

async function addMatch(dateStr, info) {
  // Format handicap display
  let handicapText = '';
  if (info.handicap > 0) {
    handicapText = `让${info.handicap}球`;
  } else if (info.handicap < 0) {
    handicapText = `受让${Math.abs(info.handicap)}球`;
  } else {
    handicapText = '平手';
  }

  const props = {
    'Name': notionTitleProp(info.matchDisplay),
    '比赛': notionRichTextProp(info.matchDisplay),
    '欧赔趋势': notionRichTextProp(info.oupei_trend),
    'IW同赔': notionRichTextProp(info.iw_tongpei),
    '澳门亚盘': notionRichTextProp(info.macau_asian),
    '主队主场': notionRichTextProp(info.home_home),
    '客队客场': notionRichTextProp(info.away_away),
    '百家对比': notionRichTextProp(info.baijia),
    '比赛日期': notionDateProp(getMatchTime(info.fid) || deriveMatchDate(dateStr, info.matchDisplay)),
    '竞彩预测': notionRichTextProp(info.pred),
    '让球预测': notionRichTextProp(info.rq_pred),
    '风险提示': notionRichTextProp(info.risk),
    '欧赔竞彩盘路': notionRichTextProp(info.oupei_jingcai_panlu),
    '欧赔interwetten盘路': notionRichTextProp(info.oupei_iw_panlu),
    '欧赔百家盘路': notionRichTextProp(info.oupei_baijia_panlu),
    '澳门亚盘盘路': notionRichTextProp(info.macau_panlu),
    '让球指数盘路': notionRichTextProp(info.rq_panlu),
    '步25_庄家盈亏': notionRichTextProp(info.s25_zjyk),
    '步26_庄家最看好': notionRichTextProp(info.s26_zzhk),
    '步26_庄家盈亏方向': notionRichTextProp(info.s26_zjyf),
    '步26_盈亏占比': notionRichTextProp(info.s26_ykbz),
    '步26_投注占比': notionRichTextProp(info.s26_tzbz),
    // 竞彩澳门亚盘（优先用meta.json的macau_line，step6作为fallback）
    '竞彩澳门亚盘': notionRichTextProp(info.macau_live || info.macau_asian_live || ''),
    '终盘竞彩澳门亚盘': notionRichTextProp(info.macau_live || info.macau_asian_live || ''),
    // 让球指数（初盘+终盘）
    '让球指数胜': { number: info.rq_win || 0 },
    '让球指数平': { number: info.rq_draw || 0 },
    '让球指数负': { number: info.rq_loss || 0 },
    // 即时盘赔率（pipeline 写入不带终盘前缀的字段）
    '竞彩欧赔胜': { number: info.jc_live_win || 0 },
    '竞彩欧赔平': { number: info.jc_live_draw || 0 },
    '竞彩欧赔负': { number: info.jc_live_loss || 0 },
    '百家欧赔胜': { number: info.bj_live_win || 0 },
    '百家欧赔平': { number: info.bj_live_draw || 0 },
    '百家欧赔负': { number: info.bj_live_loss || 0 },
    'Interwetten胜': { number: info.iw_live_win || 0 },
    'Interwetten平': { number: info.iw_live_draw || 0 },
    'Interwetten负': { number: info.iw_live_loss || 0 },
    // 终盘字段由feedback.js在次日更新，pipeline写入时清空旧值
    '终盘竞彩欧赔胜': { number: 0 },
    '终盘竞彩欧赔平': { number: 0 },
    '终盘竞彩欧赔负': { number: 0 },
    '终盘百家欧赔胜': { number: 0 },
    '终盘百家欧赔平': { number: 0 },
    '终盘百家欧赔负': { number: 0 },
    '终盘Interwetten胜': { number: 0 },
    '终盘Interwetten平': { number: 0 },
    '终盘Interwetten负': { number: 0 },
    '终盘让球指数胜': { number: 0 },
    '终盘让球指数平': { number: 0 },
    '终盘让球指数负': { number: 0 },
  };

  // 去重策略：按日期+竞彩编号(周x0xx)匹配已有行，绝不新建
  // 用matchnum推导出真实比赛日期，避免跨天比赛查错库
  const matchDateStr = deriveMatchDate(dateStr, info.matchDisplay);
  const allDay = await queryDatabase({
    property: '比赛日期',
    date: { equals: matchDateStr },
  });

  // 从 matchDisplay 提取编号: "周二008 西甲 奥萨苏纳vs马竞" → "008"
  const curNum = info.matchNum || '';

  let matched = null;
  if (curNum) {
    // 按编号精确匹配
    matched = allDay.find(p => {
      const name = p.properties['Name']?.title?.[0]?.plain_text || '';
      const m = name.match(/周[一二三四五六日](\d{3})/);
      return m && m[1] === curNum;
    });
  }
  // fallback: 按完整比赛名匹配
  if (!matched) {
    matched = allDay.find(p => {
      const name = p.properties['Name']?.title?.[0]?.plain_text || '';
      return name === info.matchDisplay;
    });
  }

  if (matched) {
    // 更新已有记录（保留反馈字段不被覆盖）
    const pageId = matched.id;
    const res = await notionRequest('PATCH', `/v1/pages/${pageId}`, { properties: props });
    if (res.status === 200) {
      console.log(`[OK] 已更新 ${info.matchDisplay}`);
      return pageId;
    } else {
      console.error(`[ERR] 更新失败: ${res.status} ${JSON.stringify(res.data).substring(0, 200)}`);
      return null;
    }
  }

  // 未匹配到已有行 → 新建记录
  const res = await notionRequest('POST', '/v1/pages', { parent: { database_id: DATABASE_ID }, properties: props });
  if (res.status === 200) {
    console.log(`[OK] 已新建 ${info.matchDisplay}`);
    return res.data.id;
  } else {
    console.error(`[ERR] 新建失败: ${res.status} ${JSON.stringify(res.data).substring(0, 200)}`);
    return null;
  }
}

async function updateMatchFeedback(pageId, score, actualResult, handicap, rq_pred, pred) {
  // Parse score (e.g. "2:1", "1:0")
  const scoreParts = score.split(':');
  let home_score = 0, away_score = 0;
  if (scoreParts.length === 2) {
    home_score = parseInt(scoreParts[0]) || 0;
    away_score = parseInt(scoreParts[1]) || 0;
  }

  // Calculate handicap result
  const rq_actual = calcHandicapResult(home_score, away_score, handicap);

  // Check predictions
  const pred_ok = checkCorrect(pred, actualResult);
  const rq_ok = checkRqCorrect(rq_pred, rq_actual, handicap);

  // Build feedback summary
  let summary = `${pred} → ${actualResult} (${score})`;
  if (rq_pred) {
    summary += `\n让球${handicap>0?'让':'受让'}${Math.abs(handicap)}球 ${rq_pred} → ${rq_actual} (${home_score}-${handicap}:${away_score})`;
  }

  const props = {
    '实际比分': notionRichTextProp(score),
    '实际结果': notionRichTextProp(actualResult),
    '反馈日期': notionDateProp(new Date(Date.now() - 86400000).toISOString().split('T')[0]),
    '反馈总结': notionRichTextProp(summary),
  };

  if (pred_ok !== null) {
    props['预测正确'] = notionCheckboxProp(pred_ok);
  }
  if (rq_ok !== null) {
    props['让球预测正确'] = notionCheckboxProp(rq_ok);
  }

  const res = await notionRequest('PATCH', `/v1/pages/${pageId}`, { properties: props });

  if (res.status === 200) {
    console.log(`[OK] 已更新反馈: ${score} ${actualResult} 让球${rq_actual}`);
    return true;
  } else {
    console.error(`[ERR] 更新失败: ${res.status} ${JSON.stringify(res.data).substring(0, 200)}`);
    return false;
  }
}

async function queryDatabase(filter) {
  const res = await notionRequest('POST', `/v1/databases/${DATABASE_ID}/query`, {
    filter,
    page_size: 100,
  });

  if (res.status === 200) {
    return res.data.results;
  } else {
    console.error(`[ERR] 查询失败: ${res.status} ${JSON.stringify(res.data).substring(0, 200)}`);
    return [];
  }
}

function getRichTextValue(page, propName) {
  const prop = page.properties[propName];
  if (!prop) return '';
  if (prop.rich_text && prop.rich_text.length > 0) {
    return prop.rich_text[0].plain_text || '';
  }
  return '';
}

function getPageId(page) {
  return page.id;
}

/**
 * From matchnum (e.g., "周三009") and the date we ran the pipeline (dateStr),
 * derive the true competition date. This prevents cross-day matches from being
 * written under the wrong date in Notion.
 */
function deriveMatchDate(dateStr, matchnum) {
  if (!matchnum) return dateStr;
  const weekdayMap = { '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 0 };
  const m = matchnum.match(/周([一二三四五六日])/);
  if (!m) return dateStr;
  const targetWeekday = weekdayMap[m[1]];
  if (targetWeekday === undefined) return dateStr;
  const d = new Date(dateStr + 'T00:00:00');
  const currentWeekday = d.getDay();
  let diff = targetWeekday - currentWeekday;
  if (diff < -4) diff += 7;
  if (diff > 4) diff -= 7;
  d.setDate(d.getDate() + diff);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

async function cmdAdd(dateStr, filterMatches) {
  const taskDir = path.join(TASKS_DIR, dateStr);
  if (!fs.existsSync(taskDir)) {
    console.log(`[WARN] 没有找到 ${dateStr} 的任务目录`);
    return;
  }

  // 先构建 matchnum→matchDir 映射表（从所有meta.json读取）
  const matchMap = {};
  const dataDir = path.join(taskDir, 'data');
  if (fs.existsSync(dataDir)) {
    const dirs = fs.readdirSync(dataDir).filter(d => {
      const dp = path.join(dataDir, d);
      return fs.existsSync(dp) && fs.statSync(dp).isDirectory() && d.startsWith('match');
    });
    for (const d of dirs) {
      const metaPath = path.join(dataDir, d, 'meta.json');
      if (!fs.existsSync(metaPath)) continue;
      try {
        const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
        const mn = meta.matchnum || '';
        // 提取编号: 周六022 → 022
        const m = mn.match(/(\d{3})/);
        if (m) {
          const num = m[1];
          const newDir = path.join(dataDir, d);
          // 检查新目录是否有 step25/step26数据
          const newHasStep25 = fs.existsSync(path.join(newDir, 'step25_zhuangjia.json'));
          const newHasStep26 = fs.existsSync(path.join(newDir, 'step26_profit_ratio.json'));
          
          if (matchMap[num]) {
            // 已有映射，检查是否应该替换
            const existingDir = matchMap[num].dir;
            const existingHasStep25 = fs.existsSync(path.join(existingDir, 'step25_zhuangjia.json'));
            const existingHasStep26 = fs.existsSync(path.join(existingDir, 'step26_profit_ratio.json'));
            // 优先选择有 step25/step26数据的目录
            const newScore = (newHasStep25 ? 1 : 0) + (newHasStep26 ? 1 : 0);
            const existingScore = (existingHasStep25 ? 1 : 0) + (existingHasStep26 ? 1 : 0);
            if (newScore > existingScore) {
              matchMap[num] = { dir: newDir, meta };
            }
          } else {
            matchMap[num] = { dir: newDir, meta };
          }
        }
      } catch(e) {}
    }
    console.log(`[INFO] 构建match映射: ${Object.keys(matchMap).length}个`);
  }
  
  // 从matchMap生成待同步列表
  const pending = [];
  for (const [num, entry] of Object.entries(matchMap)) {
    // 如果指定了过滤，只处理匹配的场次
    if (filterMatches && filterMatches.length > 0) {
      if (!filterMatches.includes(num)) continue;
    }
    pending.push({ num, matchDir: entry.dir, meta: entry.meta });
  }
  
  if (pending.length === 0) {
    console.log(`[WARN] 没有待同步的比赛`);
    return;
  }
  
  pending.sort((a, b) => a.num.localeCompare(b.num));
  console.log(`[INFO] 待同步: ${pending.length} 场 (${pending.map(p => p.num).join(',')})`);
  
  for (const p of pending) {
    const meta = p.meta || {};
    const matchNum = meta.matchnum || `周日${p.num}`;
    const home = meta.home || '';
    const away = meta.away || '';
    const reportName = `${matchNum}_${home}vs${away}.md`;
    const reportPath = path.join(taskDir, reportName);
    
    // 检查 .md 报告是否存在，不存在则自动生成
    if (!fs.existsSync(reportPath)) {
      console.log(`[REPORT] 生成报告: ${reportName}`);
      try {
        const cp = require('child_process');
        const scriptPath = path.join(JINGCAI_DIR, 'final_report_generator.py');
        const result = cp.execSync(
          'python \"' + scriptPath + '\" \"' + p.matchDir + '\" \"' + reportPath + '\"',
          { encoding: 'utf8', timeout: 300000 }
        );
        console.log(`  -> OK (${result.trim().split('\\n').filter(l => l).slice(-1)})`);
      } catch(e) {
        console.log(`  -> FAIL: ${(e.stderr || e.message || '').substring(0, 100)}`);
        // 失败则跳过同步
        continue;
      }
    }
    
    // 使用已有的 extractMatchInfo
    const info = extractMatchInfo(reportPath, p.matchDir, meta);
    await addMatch(dateStr, info);
    // 同步到 26步+结论数据库
    await syncToStepsDB(reportPath);
  }

  // === 同步后核查+自愈：检查Notion字段完整性，空字段查根因 ===
  const TEXT_FIELDS_CHECK = [
    '欧赔趋势', 'IW同赔', '澳门亚盘', '主队主场', '客队客场', '百家对比',
    '竞彩预测', '让球预测', '风险提示',
    '欧赔竞彩盘路', '欧赔interwetten盘路', '欧赔百家盘路',
    '澳门亚盘盘路', '让球指数盘路',
    '步25_庄家盈亏', '步26_庄家最看好', '步26_庄家盈亏方向', '步26_盈亏占比', '步26_投注占比',
    '竞彩澳门亚盘'
  ];
  const NUM_FIELDS_CHECK = [
    '让球指数胜', '让球指数平', '让球指数负',
    '竞彩欧赔胜', '竞彩欧赔平', '竞彩欧赔负',
    '百家欧赔胜', '百家欧赔平', '百家欧赔负',
    'Interwetten胜', 'Interwetten平', 'Interwetten负'
  ];

  function findFieldSource(matchDir, field) {
    const src = {
      '欧赔趋势': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '欧赔竞彩盘路': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '欧赔interwetten盘路': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '欧赔百家盘路': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '竞彩欧赔胜': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '竞彩欧赔平': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '竞彩欧赔负': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '百家欧赔胜': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '百家欧赔平': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      '百家欧赔负': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      'Interwetten胜': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      'Interwetten平': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      'Interwetten负': ['group01_europe', 'step1_europe_base.txt', 'step01_europe_basic.md'],
      'IW同赔': ['group01_europe', 'step3_interwetten_same.txt', 'step03_interwetten_same.md'],
      '让球指数盘路': ['group02_handicap', 'step4_handicap_base.txt', 'step04_handicap_basic.md'],
      '让球指数胜': ['group02_handicap', 'step4_handicap_base.txt', 'step04_handicap_basic.md'],
      '让球指数平': ['group02_handicap', 'step4_handicap_base.txt', 'step04_handicap_basic.md'],
      '让球指数负': ['group02_handicap', 'step4_handicap_base.txt', 'step04_handicap_basic.md'],
      '澳门亚盘盘路': ['group03_asian', 'step6_asian_base.txt', 'step06_asian_basic.md'],
      '澳门亚盘': ['group03_asian', 'step6_asian_base.txt', 'step06_asian_basic.md'],
      '竞彩澳门亚盘': ['group03_asian', 'step6_asian_base.txt', 'step06_asian_basic.md'],
      '步25_庄家盈亏': ['.', 'step25_zhuangjia.json'],
      '步26_庄家最看好': ['.', 'step26_profit_ratio.json'],
      '步26_庄家盈亏方向': ['.', 'step26_profit_ratio.json'],
      '步26_盈亏占比': ['.', 'step26_profit_ratio.json'],
      '步26_投注占比': ['.', 'step26_profit_ratio.json'],
      '主队主场': ['group04_teamA', 'step9_home_history.txt', 'step09_13_teamA.md'],
      '客队客场': ['group05_teamB', 'step14_away_history.txt', 'step14_18_teamB.md'],
      '百家对比': ['group06_baijia', 'step19_baijia_compare.txt', 'step19_23_baijia.md'],
    };
    const spec = src[field];
    if (!spec) return null;
    const grp = spec[0] === '.' ? matchDir : path.join(matchDir, spec[0]);
    for (let i = 1; i < spec.length; i++) {
      const fp = path.join(grp, spec[i]);
      if (fs.existsSync(fp)) return fp;
    }
    return null;
  }

  try {
    const vres = await notionRequest('POST', '/v1/databases/' + DATABASE_ID + '/query', {
      filter: { property: '比赛日期', date: { equals: dateStr } },
      page_size: 20
    });
    if (vres.status === 200) {
      const vpages = vres.data.results;
      let totalEmpty = 0;
      
      for (const vpage of vpages) {
        const vname = vpage.properties['Name']?.title?.[0]?.plain_text || '未知';
        let vemptyFields = [];
        const numM = vname.match(/[周][一二三四五六日](\d{3})/);
        const matchNum = numM ? numM[1] : '';

        for (const field of TEXT_FIELDS_CHECK) {
          const prop = vpage.properties[field];
          let val = '';
          if (prop?.rich_text?.length > 0) val = prop.rich_text.map(r => r.plain_text).join('').trim();
          if (!val) vemptyFields.push(field);
        }
        for (const field of NUM_FIELDS_CHECK) {
          const val = vpage.properties[field]?.number;
          if (val === null || val === undefined) vemptyFields.push(field);
        }

        if (vemptyFields.length > 0) {
          console.log('\u274c ' + vname + ': ' + vemptyFields.length + ' \u4e2a\u7a7a\u5b57\u6bb5');
          console.log('   ' + vemptyFields.join(', '));

          // 查根因
          let fieldRootCauses = {};
          for (const field of vemptyFields) {
            let matchDir = null;
            if (matchNum) {
              const dataDir2 = path.join(TASKS_DIR, dateStr, 'data');
              if (fs.existsSync(dataDir2)) {
                const dirs = fs.readdirSync(dataDir2).filter(d => d.startsWith('match'));
                for (const d of dirs) {
                  const metaP = path.join(dataDir2, d, 'meta.json');
                  if (fs.existsSync(metaP)) {
                    try {
                      const meta = JSON.parse(fs.readFileSync(metaP, 'utf8'));
                      const mn = meta.matchnum || '';
                      if (mn.includes(matchNum)) {
                        matchDir = path.join(dataDir2, d);
                        break;
                      }
                    } catch(e) {}
                  }
                }
              }
            }
            if (!matchDir) {
              fieldRootCauses[field] = '无match目录(' + (matchNum || '?') + ')';
              continue;
            }
            const srcFile = findFieldSource(matchDir, field);
            if (!srcFile) {
              fieldRootCauses[field] = '无源文件映射';
              continue;
            }
            if (!fs.existsSync(srcFile)) {
              fieldRootCauses[field] = '源文件不存在: ' + path.basename(srcFile);
              continue;
            }
            const st = fs.statSync(srcFile);
            if (st.size < 20) {
              fieldRootCauses[field] = '源文件过小(' + st.size + 'B): ' + path.basename(srcFile);
              continue;
            }
            fieldRootCauses[field] = '提取逻辑未命中: ' + path.basename(srcFile) + ' 存在(' + st.size + 'B)';
          }

          const logged = {};
          for (const [f, c] of Object.entries(fieldRootCauses)) {
            if (!logged[c]) logged[c] = [];
            logged[c].push(f);
          }
          for (const [cause, fields] of Object.entries(logged)) {
            console.log('   \uD83D\uDD0D ' + fields.join(', ') + ' -> ' + cause);
          }
          totalEmpty += vemptyFields.length;
        } else {
          console.log('\u2705 ' + vname + ': \u5168\u90e8\u5b57\u6bb5\u6709\u6570\u636e');
        }
      }
      if (totalEmpty > 0) {
        console.log('\n\u26a0\ufe0f  FLAG: \u5171\u8ba1 ' + totalEmpty + ' \u4e2a\u7a7a\u5b57\u6bb5\uff0c\u6839\u56e0\u5df2\u6807\u6ce8');
      } else {
        console.log('\n\u2705 \u6240\u6709\u5b57\u6bb5\u540c\u6b65\u5b8c\u6574');
      }
    } else {
      console.log('[WARN] \u540c\u6b65\u540e\u6838\u67e5\u67e5\u8be2\u5931\u8d25: ' + vres.status);
    }
  } catch(e) {
    console.log('[WARN] \u540c\u6b65\u540e\u6838\u67e5\u5f02\u5e38: ' + e.message);
  }
}


async function cmdUpdateFeedback(dateStr) {
  const resultsPath = path.join(JINGCAI_DIR, `results_${dateStr}.json`);
  if (!fs.existsSync(resultsPath)) {
    console.log(`[WARN] 没有找到 ${dateStr} 的赛果`);
    return;
  }
  
  const results = JSON.parse(fs.readFileSync(resultsPath, 'utf8'))[dateStr] || {};
  
  const pages = await queryDatabase({
    property: '比赛日期',
    date: { equals: dateStr },
  });
  
  // Load report files to extract handicap
  const taskDir = path.join(TASKS_DIR, dateStr);
  const reportFiles = fs.existsSync(taskDir) ? fs.readdirSync(taskDir).filter(f => f.endsWith('.md')) : [];
  const reportMap = {};
  for (const rf of reportFiles) {
    const numMatch = rf.match(/周[一二三四五六日](\d{3})/);
    if (numMatch) {
      const content = fs.readFileSync(path.join(taskDir, rf), 'utf8');
      // Extract handicap from let球指数明细 table
      let handicap = 0;
      const rqTable = content.match(/\|\s*竞彩官方\s*\|\s*([+-]?\d+(?:\.5)?)\s*\|/);
      if (rqTable) {
        handicap = -parseFloat(rqTable[1]);  // 取反：-1→1(让球), 1→-1(受让)
      }
      reportMap[numMatch[1]] = handicap;
    }
  }
  
  console.log(`[INFO] 找到 ${pages.length} 场 Notion 记录，赛果 ${Object.keys(results).length} 场`);
  
  for (const page of pages) {
    const matchText = getRichTextValue(page, '比赛');
    const numMatch = matchText.match(/(\d{3})/);
    const num = numMatch ? numMatch[1].padStart(3, '0') : '';
    
    if (results[num]) {
      const score = results[num].score || '待查';
      const actualResult = results[num].result || '待查';
      
      const pred = getRichTextValue(page, '竞彩预测');
      const rq_pred = getRichTextValue(page, '让球预测');
      
      // 从报告文件中获取让球数
      const handicap = reportMap[num] || 0;

      // 计算让球后的实际结果
      const scoreParts = score.split(':');
      let rq_actual = '待查';
      if (scoreParts.length === 2 && handicap !== 0) {
        const home_score = parseInt(scoreParts[0]) || 0;
        const away_score = parseInt(scoreParts[1]) || 0;
        rq_actual = calcHandicapResult(home_score, away_score, handicap);
      } else {
        rq_actual = actualResult;
      }

      const pred_ok = checkCorrect(pred, actualResult);
      const rq_ok = checkRqCorrect(rq_pred, rq_actual, handicap);

      // 构建反馈总结
      let summary = `${pred} → ${actualResult} (${score})`;
      if (rq_pred && handicap !== 0) {
        const scoreParts = score.split(':');
        if (scoreParts.length === 2) {
          const home_score = parseInt(scoreParts[0]) || 0;
          const away_score = parseInt(scoreParts[1]) || 0;
          summary += `\n让球${handicap>0?'让':'受让'}${Math.abs(handicap)}球 ${rq_pred} → ${rq_actual} (${home_score-handicap}:${away_score})`;
        }
      } else if (rq_pred) {
        summary += `\n让球平 ${rq_pred} → ${actualResult}`;
      }

      await updateMatchFeedback(
        getPageId(page),
        score,
        actualResult,
        handicap,
        rq_pred,
        pred
      );
    }
  }
}

async function main() {
  const cmd = process.argv[2];
  const dateStr = process.argv[3];
  const filterArg = process.argv[4];

  if (!cmd || !dateStr) {
    console.log('用法:');
    console.log('  node sync_notion.js add <date>                  # 添加当天全部比赛');
    console.log('  node sync_notion.js add <date> 001              # 只添加周日001');
    console.log('  node sync_notion.js add <date> 001,005,012      # 添加指定场次');
    console.log('  node sync_notion.js feedback <date>             # 更新反馈');
    process.exit(1);
  }

  try {
    if (cmd === 'add') {
      let filterMatches = null;
      if (filterArg) {
        filterMatches = filterArg.split(',').map(s => s.trim().padStart(3, '0')).filter(s => s);
      }
      await cmdAdd(dateStr, filterMatches);
    } else if (cmd === 'feedback') {
      await cmdUpdateFeedback(dateStr);
    } else {
      console.error(`未知命令: ${cmd}`);
      process.exit(1);
    }
  } catch (e) {
    console.error(`[ERR] ${e.message}`);
    process.exit(1);
  }
}
main();
