"""日志工具 - 统一日志模块"""
import os, sys, io, time, logging, traceback
from datetime import datetime

def setup_logger(name, log_dir=None, level=logging.INFO, console=True):
    """创建统一格式的logger
    
    用法:
        from _log_util import setup_logger
        log = setup_logger('step7', 'tasks/2026-05-17/logs')
        log.info('开始获取...')
        log.warning('数据为空')
        log.error('获取失败: xxx')
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] %(levelname)s %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 控制台输出（可选，默认开启）
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    # 文件输出
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(
            os.path.join(log_dir, '%s.log' % name),
            encoding='utf-8'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger
