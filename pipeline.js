#!/usr/bin/env node
/**
 * 竞彩数据流水线 - 主入口
 * 
 * 用法:
 *   node pipeline.js sync [date]     # 同步指定日期的竞彩数据到 Notion
 *   node pipeline.js feedback [date] # 更新反馈（获取赛果）
 *   node pipeline.js report [week]   # 生成周报
 *   node pipeline.js archive [date]  # 归档数据到统一目录
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const SCRIPT_DIR = __dirname;
const DATA_DIR = path.join(__dirname, '..', 'data');

function run(cmd, options = {}) {
    console.log(`\n▶ ${cmd}`);
    try {
        const result = execSync(cmd, { 
            cwd: options.cwd || SCRIPT_DIR,
            stdio: 'inherit',
            timeout: options.timeout || 300000
        });
        return { success: true };
    } catch (err) {
        console.error(`❌ 执行失败: ${err.message}`);
        return { success: false, error: err.message };
    }
}

async function main() {
    const args = process.argv.slice(2);
    const command = args[0];
    
    console.log('='.repeat(60));
    console.log('📊 竞彩数据流水线');
    console.log('='.repeat(60));
    
    switch (command) {
        case 'sync':
            // 同步竞彩数据到 Notion
            const syncDate = args[1] || new Date().toISOString().split('T')[0];
            console.log(`\n📅 同步日期: ${syncDate}`);
            
            // 1. 获取比赛列表
            console.log('\n[1/3] 获取竞彩比赛列表...');
            run(`python "${path.join(SCRIPT_DIR, 'step0_fetch_matches.py')}" --date ${syncDate}`);
            
            // 2. 运行竞彩流水线
            console.log('\n[2/3] 运行竞彩分析流水线...');
            run(`python "${path.join(SCRIPT_DIR, 'run_pipeline.py')}" ${syncDate}`);
            
            // 3. 同步到 Notion
            console.log('\n[3/3] 同步到 Notion...');
            run(`node "${path.join(SCRIPT_DIR, 'sync_notion.js')}" add ${syncDate}`);
            
            console.log('\n✅ 同步完成');
            break;
            
        case 'feedback':
            // 更新反馈
            const feedbackDate = args[1] || new Date(Date.now() - 86400000).toISOString().split('T')[0];
            console.log(`\n📅 反馈日期: ${feedbackDate}`);
            
            run(`node "${path.join(SCRIPT_DIR, 'feedback.js')}" --date ${feedbackDate}`);
            
            console.log('\n✅ 反馈更新完成');
            break;
            
        case 'report':
            // 生成周报
            const weekOffset = parseInt(args[1]) || 0;
            console.log(`\n📅 周报: ${weekOffset === 0 ? '本周' : `${weekOffset} 周前`}`);
            
            run(`node "${path.join(SCRIPT_DIR, 'weekly_report.js')}" --week ${weekOffset}`);
            
            console.log('\n✅ 周报生成完成');
            break;
            
        case 'archive':
            // 归档数据
            const archiveDate = args[1];
            console.log(`\n📅 归档日期: ${archiveDate || '全部'}`);
            
            const tasksDir = path.join(SCRIPT_DIR, 'tasks');
            const archiveDir = path.join(DATA_DIR, 'jingcai', 'tasks');
            
            if (!fs.existsSync(archiveDir)) {
                fs.mkdirSync(archiveDir, { recursive: true });
            }
            
            if (archiveDate) {
                // 归档指定日期
                const src = path.join(tasksDir, archiveDate);
                const dst = path.join(archiveDir, archiveDate);
                
                if (fs.existsSync(src)) {
                    fs.cpSync(src, dst, { recursive: true });
                    console.log(`✅ 已归档: ${archiveDate}`);
                } else {
                    console.log(`⚠️ 未找到: ${archiveDate}`);
                }
            } else {
                // 归档全部
                const dates = fs.readdirSync(tasksDir).filter(f => {
                    const stat = fs.statSync(path.join(tasksDir, f));
                    return stat.isDirectory() && f.match(/^\d{4}-\d{2}-\d{2}$/);
                });
                
                for (const date of dates) {
                    const src = path.join(tasksDir, date);
                    const dst = path.join(archiveDir, date);
                    
                    if (!fs.existsSync(dst)) {
                        fs.cpSync(src, dst, { recursive: true });
                        console.log(`✅ 已归档: ${date}`);
                    }
                }
                
                console.log(`\n✅ 共归档 ${dates.length} 个日期`);
            }
            
            break;
            
        case 'full':
            // 完整日更流程
            const fullDate = args[1] || new Date().toISOString().split('T')[0];
            console.log(`\n📅 完整流程日期: ${fullDate}`);
            
            console.log('\n[1/5] 获取今日竞彩比赛列表...');
            run(`python "${path.join(SCRIPT_DIR, 'step0_fetch_matches.py')}" --date ${fullDate}`);
            
            console.log('\n[2/5] 运行竞彩分析流水线...');
            run(`python "${path.join(SCRIPT_DIR, 'run_pipeline.py')}" ${fullDate}`);
            
            console.log('\n[3/5] 同步到 Notion...');
            run(`node "${path.join(SCRIPT_DIR, 'sync_notion.js')}" add ${fullDate}`);
            
            console.log('\n[4/5] 更新反馈...');
            const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
            run(`node "${path.join(SCRIPT_DIR, 'feedback.js')}" --date ${yesterday}`);
            
            console.log('\n[5/5] 归档数据...');
            run(`node "${path.join(SCRIPT_DIR, 'pipeline.js')}" archive ${fullDate}`);
            
            console.log('\n✅ 完整流程完成');
            break;
            
        default:
            console.log(`
竞彩数据流水线

用法:
  node pipeline.js sync [date]       同步竞彩数据到 Notion
  node pipeline.js feedback [date]   更新反馈（获取赛果）
  node pipeline.js report [week]     生成周报 (0=本周, -1=上周)
  node pipeline.js archive [date]    归档数据到统一目录
  node pipeline.js full [date]       完整日更流程

示例:
  node pipeline.js sync 2026-05-01
  node pipeline.js feedback
  node pipeline.js report 0
  node pipeline.js full 2026-05-01
`);
    }
}

main().catch(err => {
    console.error('[FATAL]', err.message);
    process.exit(1);
});
