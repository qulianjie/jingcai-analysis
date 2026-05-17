#!/usr/bin/env node
/**
 * 竞彩 cron 守护脚本
 * 
 * 纯脚本执行，不依赖 AI——
 * 1. 真正执行 pipeline
 * 2. 捕获真实输出
 * 3. 生成报告推送到钉钉
 * 
 * 用法: node jingcai/cron_guardian.js
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const SCRIPT_DIR = __dirname;
const today = new Date().toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' }).replace(/\//g, '-');

function run(cmd, timeout = 3600000) {
    console.log(`\n▶ 执行: ${cmd}`);
    try {
        const output = execSync(cmd, {
            cwd: SCRIPT_DIR,
            encoding: 'utf8',
            timeout: timeout,
            maxBuffer: 10 * 1024 * 1024
        });
        console.log(output.slice(-500)); // 只打印最后500行
        return { success: true, output };
    } catch (err) {
        console.error(`❌ 失败: ${err.message}`);
        return { success: false, output: err.stdout || err.stderr || err.message };
    }
}

async function main() {
    console.log('📊 竞彩 cron 守护脚本');
    console.log(`📅 日期: ${today}\n`);
    
    // 第1步：执行 pipeline
    const result = run(`node "${path.join(SCRIPT_DIR, 'pipeline.js')}" full --date ${today}`);
    
    if (!result.success) {
        console.error('Pipeline 执行失败');
        process.exit(1);
    }
    
    // 第2步：检查真实文件
    const tasksDir = path.join(SCRIPT_DIR, 'tasks', today);
    const reports = fs.existsSync(tasksDir) 
        ? fs.readdirSync(tasksDir).filter(f => f.endsWith('.md'))
        : [];
    
    console.log(`\n✅ 找到 ${reports.length} 份报告`);
    reports.forEach(r => console.log(`  - ${r}`));
    
    // 第3步：读取最终报告内容
    const summary = reports.length > 0
        ? reports.map(r => `  📄 ${r}`).join('\n')
        : '  ⚠️ 无比赛数据';
    
    // 输出到钉钉
    console.log(`\n--- 最终报告 ---`);
    console.log(`📊 竞彩流水线完成 | ${today}`);
    console.log(`报告数量: ${reports.length}`);
    console.log(`\n${summary}`);
    console.log(`\n--- Pipeline 原始输出末尾 ---`);
    console.log(result.output.slice(-2000)); // 最后2000字符
}

main().catch(err => {
    console.error('致命错误:', err);
    process.exit(1);
});
