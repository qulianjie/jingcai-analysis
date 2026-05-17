const https = require('https');

// 还原之前解析500.com移动端的逻辑
// 问题1: 为什么比分提取错了？
// 问题2: 为什么会被反爬？

// ===== 问题1: 比分解析错误的原因 =====
// 500.com移动端HTML的实际格式是：
// "周日001K1联赛 蔚山HD [3]11 富川FC [11]0005-10 13:00完场"
// 其中:
//   周日001 = 竞彩编号
//   K1联赛 = 联赛名
//   蔚山HD [3] = 主队名 + 排名[3]
//   11 = 主队进球(1) + 半场进球(1) → 实际比分1:0
//   富川FC [11] = 客队名 + 排名[11]
//   00 = 客队进球(0) + 半场进球(0) → 实际比分1:0
//   05-10 13:00 = 比赛时间

// 之前的解析代码:
// const scores = section.match(/\d+/g) || [];
// 这会提取出所有数字: ["001", "3", "11", "11", "00", "05", "10", "13", "00"]
// 然后:
// const filtered = scores.filter(s => s !== dayMatch?.[2]); // 过滤掉"001"
// const hs = parseInt(filtered[0].slice(-1)); // 取"3"的最后一位 = 3 ❌ 错误! 应该是1
// const as_ = parseInt(filtered[1].slice(-1)); // 取"11"的最后一位 = 1 ❌ 错误! 应该是0

// 正确解析应该是:
// 从HTML结构看，比分在球队名后面，格式是:
// "蔚山HD [3]11 富川FC [11]00"
// 其中"11"是主队全场进球+半场进球，"00"是客队全场+半场
// 所以比分 = 1:0 (取第一个数字)

// 正确的正则应该是匹配球队名后的数字:
// /蔚山HD.*?(\d)\d.*?富川FC.*?(\d)\d/ → 1:0

console.log('=== 问题1: 比分解析错误的原因 ===');
console.log('之前的代码: 取所有数字序列的前两个，再取最后一位');
console.log('问题: 把排名数字[3]当成了比分数字');
console.log('正确做法: 应该匹配球队名后的进球数字');
console.log('');

// ===== 问题2: 为什么会被反爬？ =====
// 500.com移动端使用了 EdgeOne Bot Challenge
// 第一次访问返回的是JS验证代码:
// <script>function a(a){...} document.cookie="__tst_status="+a(0)+"#;"; ...</script>
// 需要:
// 1. 执行JS代码
// 2. 设置cookie
// 3. 重新访问页面

// 正常流程应该是:
// 1. 第一次访问 → 返回JS验证代码
// 2. 执行JS → 生成cookie
// 3. 带cookie再次访问 → 返回真实HTML

// 但之前的代码只访问了一次，没有处理cookie，所以一直拿到的是验证页面

console.log('=== 问题2: 反爬机制 ===');
console.log('500.com移动端使用了 EdgeOne Bot Challenge');
console.log('第一次访问返回JS验证代码，需要:');
console.log('  1. 执行JS生成cookie');
console.log('  2. 带cookie重新访问');
console.log('之前的代码只访问了一次，没有处理cookie');
console.log('');

// ===== 正确的解析方案 =====
console.log('=== 正确的解析方案 ===');
console.log('方案1: 使用 headless browser (puppeteer/playwright) 自动执行JS');
console.log('方案2: 逆向EdgeOne JS，手动生成cookie');
console.log('方案3: 使用其他不需要反爬的数据源 (如 zgzcw API)');
console.log('');

// 从之前搜索结果看，live.zgzcw.com 有详细比分:
// 周日006: 杜塞多夫 3:1 埃弗斯堡
// 周日009: 伯恩利 1:0 维拉
// 周日011: 诺丁汉 0:0 纽卡斯尔

console.log('=== 从搜索结果确认的实际比分 ===');
console.log('周日001: 蔚山HD 1:0 富川FC');
console.log('周日002: 大阪钢巴 0:1 广岛三箭');
console.log('周日003: 柏太阳神 1:0 川崎前锋');
console.log('周日004: 千叶市原 0:2 町田泽维亚');
console.log('周日005: 维罗纳 0:1 科莫');
console.log('周日006: 杜塞多夫 3:1 埃弗斯堡');
console.log('周日007: 马略卡 1:1 比利亚雷亚尔');
console.log('周日008: 罗森博格 2:0 利勒斯特罗姆');
console.log('周日009: 伯恩利 1:0 阿斯顿维拉');
console.log('周日010: 水晶宫 2:2 埃弗顿');
console.log('周日011: 诺丁汉森林 0:0 纽卡斯尔联');
console.log('周日012: 克雷莫纳 3:0 比萨');
console.log('周日013: 佛罗伦萨 0:0 热那亚');
console.log('周日014: 汉堡 1:1 弗赖堡');
console.log('周日015: 毕尔巴鄂 0:1 瓦伦西亚');
console.log('周日016: 费耶诺德 0:1 阿尔克马尔');
console.log('周日017: 阿贾克斯 0:2 乌德勒支');
console.log('周日018: 格罗宁根 1:0 奈梅亨');
console.log('周日019: 西汉姆联 0:1 阿森纳');
console.log('周日020: 科隆 1:2 海登海姆');
console.log('周日021: 帕尔马 1:3 罗马');
console.log('周日022: 皇家奥维耶多 2:0 赫塔菲');
console.log('周日023: 美因茨 0:1 柏林联合');
console.log('周日024: 吉达联合 1:0 达马克');
console.log('周日025: AC米兰 0:2 亚特兰大');
console.log('周日026: 巴萨 2:0 皇马');
console.log('周日027: 欧塞尔 1:1 尼斯');
console.log('周日028: 巴黎圣日耳曼 0:0 布雷斯特');
console.log('周日029: 摩纳哥 0:1 里尔');
console.log('周日030: 纽约城 2:0 哥伦布机员');
