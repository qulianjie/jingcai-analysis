#!/usr/bin/env node
/**
 * 并行补5月7日~5月16日终盘数据
 * 对每天调用 feedback.js --date YYYY-MM-DD
 * 但跳过赛果查询（只补终盘赔率，不更新赛果）
 * 不带--date时默认补5-7到5-16全部
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const DATES = [];
for (let d = 7; d <= 16; d++) {
    DATES.push(`2026-05-${String(d).padStart(2, '0')}`);
}

console.log('=== 批量终盘补数据 ===');
console.log(`待处理: ${DATES.join(', ')}`);
console.log('');

let ok = 0, fail = 0;
for (const date of DATES) {
    process.stdout.write(`[${date}] `);
    try {
        const r = execSync(`node feedback.js --date ${date}`, {
            cwd: __dirname,
            timeout: 120000,
            stdio: ['pipe', 'pipe', 'pipe']
        });
        const out = r.toString();
        // 提取关键信息
        const lines = out.split('\n').filter(l => 
            l.includes('[终盘]') || 
            l.includes('已更新') || 
            l.includes('已跳过') || 
            l.includes('✅') ||
            l.includes('❌')
        );
        lines.forEach(l => process.stdout.write(`  ${l.trim()}\n`));
        console.log(`  ✅ OK`);
        ok++;
    } catch (e) {
        const msg = e.stderr ? e.stderr.toString().slice(0, 200) : e.message;
        console.log(`  ❌ ${msg}`);
        fail++;
    }
}

console.log(`\n完成: ${ok} OK, ${fail} FAIL`);
