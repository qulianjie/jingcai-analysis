// Quick test: does extractScoreFromTable find 澳门亚盘?
const fs = require('fs');
const path = require('path');

const reportPath = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15/周五001_阿德莱德vs奥克兰FC.md';
const content = fs.readFileSync(reportPath, 'utf8');

// Same regex as in sync_notion.js
function extractScoreFromTable(text, label) {
    if (label === '澳门亚盘') {
        // 从结论部分(第九部分)提取澳门亚盘趋势
        const conclusionSection = text.match(/# [\u4e5d9][\u90e8\u9879\u5206\u7ae0][\s\S]*?(?=# [^\u4e5d9]|$)/);
        if (conclusionSection) {
            const m = conclusionSection[0].match(/\|\s*澳门亚盘\s*\|\s*([^|]+)\|\s*([^|]+)\|/);
            if (m) {
                return m[1].trim() + ' | ' + m[2].trim();
            }
            console.log('conclusionSection found, first regex no match');
        } else {
            console.log('No conclusionSection found (regex # [九9][部分章])');
            // Try to find what's actually there
            const alt = content.match(/# [\s\S]{0,50}最终|结论[\s\S]{0,50}/);
            if (alt) console.log('Alt match:', alt[0].substring(0, 100));
        }
        // fallback: 从全文匹配带趋势关键词的行
        const trendM = text.match(/\|\s*澳门亚盘\s*\|\s*([+-][\d.]+\s+利好[主客])\s*\|\s*([\d.]+%)\s*\|/);
        if (trendM) {
            return trendM[1].trim() + ' | ' + trendM[2].trim();
        }
        console.log('fallback trendM also no match');
        // Just try any match
        const anyM = text.match(/\|\s*澳门亚盘\s*\|([^|]+)\|([^|]+)\|/);
        if (anyM) {
            console.log('Any regex matched:', anyM[0]);
        }
        return '';
    }
    return '';
}

const result = extractScoreFromTable(content, '澳门亚盘');
console.log('Result:', result || '(empty)');

// Find line with 澳门亚盘
const lines = content.split('\n').filter(l => l.includes('澳门亚盘') && l.includes('|'));
console.log('\nLines with 澳门亚盘 and |:');
lines.forEach(l => console.log('  [' + l.trim() + ']'));
