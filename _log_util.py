# -*- coding: utf-8 -*-
"""统一日志工具
用法:
    from _log_util import setup_logger
    log = setup_logger('step7', 'tasks/2026-05-17/logs')
    log.info('开始获取...')
    log.warning('数据为空')
    log.error('获取失败: xxx')
"""
import os, sys, io, time, logging, traceback
from datetime import datetime

def setup_logger(name, log_dir=None, console=True):
    """创建带标准格式的logger
    
    Args:
        name: logger名称
        log_dir: 日志文件目录（可选），如果提供则在目录下创建 {name}.log
        console: 是否输出到控制台（默认True），设为False则仅写文件
    
    Returns:
        logging.Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 避免重复handler
    if logger.handlers:
        return logger
    
    # 控制台handler（除非console=False）
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] %(levelname)s %(message)s',
            datefmt='%H:%M:%S'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    # 文件handler（如果提供了日志目录）
    if log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
            fh = logging.FileHandler(
                os.path.join(log_dir, f'{name}.log'),
                encoding='utf-8'
            )
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass
    
    return logger
