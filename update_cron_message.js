#!/usr/bin/env node
/**
 * 更新竞彩 cron 的 message，防止 AI 想象结果
 * 
 * 用法: node jingcai/update_cron_message.js
 */

const fs = require('fs');
const path = require('path');

const CRON_FILE = path.join(process.env.USERPROFILE, '.openclaw', 'cron', 'jobs.json');
const CRON_ID = 'a99916ec-f7b9-4792-969c-972d91c66f9d';

const NEW_MESSAGE = `竞彩流水线任务。执行完成后把结果推送到钉钉群 200755295026494404。

【铁律：禁止想象、编造、概括结果】

你必须按顺序真正执行以下命令，每步执行后把【完整原始输出】粘贴到报告里：

=== 第1步：获取比赛列表 ===
执行: node jingcai/pipeline.js full
必须输出: 命令的完整原始输出（不能省略、不能概括）

=== 第2步：校验数据真实性 ===
执行: Get-ChildItem jingcai/tasks/$(Get-Date -Format yyyy-MM-dd)/*.md -ErrorAction SilentlyContinue
执行: Get-ChildItem jingcai/tasks/$(Get-Date -Format yyyy-MM-dd)/data/match*/meta.json -ErrorAction SilentlyContinue
必须输出: 文件列表完整内容

=== 第3步：输出最终报告 ===
基于真实文件内容输出摘要，不能编造数据

【禁止行为】
❌ 不能说"执行成功"而不贴原始输出
❌ 不能自己编造比分或预测结果
❌ 不能用"摘要""概括"代替真实命令输出
❌ 不能跳过任何校验步骤

【如果命令失败】
- 把完整错误信息原样粘贴
- 不要编造原因，不要猜测
- 报告实际看到的错误`;

try {
    const content = fs.readFileSync(CRON_FILE, 'utf8');
    const jobs = JSON.parse(content);
    
    const job = jobs.jobs.find(j => j.id === CRON_ID);
    if (!job) {
        console.error(`❌ 未找到 cron ${CRON_ID}`);
        process.exit(1);
    }
    
    job.payload.message = NEW_MESSAGE;
    job.updatedAtMs = Date.now();
    
    // 备份
    const bakFile = CRON_FILE + '.bak_' + Date.now();
    fs.copyFileSync(CRON_FILE, bakFile);
    console.log(`✅ 已备份到: ${bakFile}`);
    
    console.log(`✅ Cron ${CRON_ID} 的 message 已更新`);
    console.log(`\n新 message 长度: ${NEW_MESSAGE.length} 字符`);
    
    // 修复 toolsAllow 格式：从 ["exec read write"] 改为 ["exec", "read", "write"]
    if (job.toolsAllow) {
        console.log(`\n当前 toolsAllow: ${JSON.stringify(job.toolsAllow)}`);
        job.toolsAllow = job.toolsAllow[0].split(/\s+/);
        console.log(`修复后 toolsAllow: ${JSON.stringify(job.toolsAllow)}`);
    }
    
    // 修复 delivery 格式
    job.delivery = {
        mode: 'announce',
        target: 'group:200755295026494404'
    };
    console.log(`\n修复 delivery 格式: ${JSON.stringify(job.delivery)}`);
    
    // 写入
    fs.writeFileSync(CRON_FILE, JSON.stringify(jobs, null, 2), 'utf8');
    console.log(`\n✅ 文件已保存`);
    
} catch (err) {
    console.error('❌ 更新失败:', err.message);
    process.exit(1);
}
