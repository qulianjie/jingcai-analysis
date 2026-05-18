/**
 * 日志工具模块 — JS 统一日志
 * 给 feedback.js / sync_notion.js 等 JS 脚本使用
 * 
 * 用法:
 *   const log = require('./_log_util.js');
 *   log.info('feedback', '开始处理...');
 *   log.warn('feedback', '数据不完整');
 *   log.error('feedback', '连接失败');
 *   // 写文件: log.setLogDir('/path/to/logs');
 */

const fs = require('fs');
const path = require('path');

let _logDir = null;

function timestamp() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

function log(level, tag, msg) {
  const ts = timestamp();
  const line = `[${ts}] [${tag}] ${level} ${msg}`;
  console.log(line);
  
  if (_logDir) {
    const logFile = path.join(_logDir, `${tag}.log`);
    try {
      fs.appendFileSync(logFile, line + '\n', 'utf8');
    } catch (e) {
      // silent
    }
  }
}

module.exports = {
  info: (tag, msg) => log('INFO', tag, msg),
  warn: (tag, msg) => log('WARN', tag, msg),
  error: (tag, msg) => log('ERROR', tag, msg),
  debug: (tag, msg) => log('DEBUG', tag, msg),
  
  setLogDir: (dirPath) => {
    _logDir = dirPath;
    if (dirPath && !fs.existsSync(dirPath)) {
      try { fs.mkdirSync(dirPath, { recursive: true }); } catch(e) {}
    }
  },
  
  setLogDirFromMeta: (matchDir) => {
    if (matchDir && fs.existsSync(matchDir)) {
      const logsDir = path.join(path.dirname(path.normalize(matchDir)), 'logs');
      module.exports.setLogDir(logsDir);
    }
  }
};
