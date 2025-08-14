#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
提供统一的日志配置和管理功能
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（仅在终端中有效）"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'  # 重置
    }

    def format(self, record):
        # 获取原始格式
        log_message = super().format(record)

        # 如果不是终端环境，直接返回
        if not sys.stderr.isatty():
            return log_message

        # 添加颜色
        level_name = record.levelname
        if level_name in self.COLORS:
            colored_level = f"{self.COLORS[level_name]}{level_name}{self.COLORS['RESET']}"
            log_message = log_message.replace(level_name, colored_level, 1)

        return log_message


def setup_logger(name: str = None,
                 log_level: str = 'INFO',
                 log_to_file: bool = True,
                 log_to_console: bool = True,
                 log_dir: str = None) -> logging.Logger:
    """
    设置日志系统

    Args:
        name: 日志器名称，None表示根日志器
        log_level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file: 是否记录到文件
        log_to_console: 是否输出到控制台
        log_dir: 日志文件目录，None表示使用默认目录

    Returns:
        配置好的日志器
    """
    # 创建或获取日志器
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if log_to_file:
        # 确定日志目录
        if log_dir is None:
            log_dir = Path.home() / '.comtrade_analyzer' / 'logs'
        else:
            log_dir = Path(log_dir)

        # 创建日志目录
        log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件名包含日期
        log_filename = f"comtrade_analyzer_{datetime.now().strftime('%Y%m%d')}.log"
        log_file_path = log_dir / log_filename

        # 创建旋转文件处理器（每天一个文件，保留30天）
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file_path),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 创建错误日志文件处理器
        error_log_filename = f"comtrade_analyzer_error_{datetime.now().strftime('%Y%m%d')}.log"
        error_log_file_path = log_dir / error_log_filename

        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(error_log_file_path),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    # 防止重复记录
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    return logging.getLogger(name)


class LogCapture:
    """日志捕获器，用于在GUI中显示日志"""

    def __init__(self, level: int = logging.INFO):
        self.level = level
        self.logs = []
        self.max_logs = 1000  # 最大保存的日志条数

        # 创建处理器
        self.handler = logging.Handler()
        self.handler.setLevel(level)
        self.handler.emit = self._emit

        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)

    def _emit(self, record):
        """处理日志记录"""
        try:
            # 格式化日志消息
            message = self.handler.format(record)

            # 添加到日志列表
            self.logs.append({
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.name
            })

            # 限制日志数量
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]

        except Exception:
            pass  # 忽略日志处理错误

    def get_logs(self, level: Optional[str] = None,
                 limit: Optional[int] = None) -> list:
        """
        获取日志记录

        Args:
            level: 日志级别过滤
            limit: 限制返回数量

        Returns:
            日志记录列表
        """
        logs = self.logs

        # 级别过滤
        if level:
            logs = [log for log in logs if log['level'] == level.upper()]

        # 数量限制
        if limit:
            logs = logs[-limit:]

        return logs

    def clear_logs(self):
        """清空日志"""
        self.logs.clear()

    def export_logs(self, file_path: str, level: Optional[str] = None):
        """
        导出日志到文件

        Args:
            file_path: 输出文件路径
            level: 日志级别过滤
        """
        logs = self.get_logs(level)

        with open(file_path, 'w', encoding='utf-8') as f:
            for log in logs:
                timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log['level']} - {log['module']} - {log['message']}\n")


class PerformanceLogger:
    """性能日志记录器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}

    def start_timer(self, name: str):
        """开始计时"""
        self.timers[name] = datetime.now()
        self.logger.debug(f"开始计时: {name}")

    def end_timer(self, name: str, log_level: str = 'INFO'):
        """结束计时并记录"""
        if name not in self.timers:
            self.logger.warning(f"未找到计时器: {name}")
            return

        start_time = self.timers.pop(name)
        elapsed = (datetime.now() - start_time).total_seconds()

        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.log(level, f"性能统计 - {name}: {elapsed:.4f}秒")

        return elapsed

    def log_memory_usage(self):
        """记录内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            self.logger.info(f"内存使用 - RSS: {memory_info.rss / 1024 / 1024:.2f}MB, "
                             f"VMS: {memory_info.vms / 1024 / 1024:.2f}MB")
        except ImportError:
            self.logger.warning("psutil未安装，无法记录内存使用情况")


# 创建全局性能日志器
_performance_logger = None


def get_performance_logger() -> PerformanceLogger:
    """获取全局性能日志器"""
    global _performance_logger
    if _performance_logger is None:
        logger = get_logger('performance')
        _performance_logger = PerformanceLogger(logger)
    return _performance_logger


def log_exception(logger: logging.Logger, message: str = "发生异常"):
    """
    记录异常信息的装饰器工厂

    Args:
        logger: 日志器
        message: 异常消息前缀
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{message}: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def timed_operation(logger: logging.Logger, operation_name: str = None):
    """
    记录操作耗时的装饰器

    Args:
        logger: 日志器
        operation_name: 操作名称
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"操作完成 - {name}: {elapsed:.4f}秒")
                return result
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.error(f"操作失败 - {name}: {elapsed:.4f}秒, 错误: {e}")
                raise

        return wrapper

    return decorator


# 预定义的日志器
def get_app_logger() -> logging.Logger:
    """获取应用主日志器"""
    return get_logger('comtrade_analyzer')


def get_analysis_logger() -> logging.Logger:
    """获取分析模块日志器"""
    return get_logger('comtrade_analyzer.analysis')


def get_gui_logger() -> logging.Logger:
    """获取GUI模块日志器"""
    return get_logger('comtrade_analyzer.gui')


def get_core_logger() -> logging.Logger:
    """获取核心模块日志器"""
    return get_logger('comtrade_analyzer.core')