#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMTRADE波形分析器主程序入口
作者: [您的名字]
版本: 2.0.0
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入PyQt6
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QFont, QPalette, QColor

# 导入项目模块
from config.settings import AppSettings
from utils.logger import setup_logger
from gui.main_window import MainWindow


def check_dependencies():
    """检查必要的依赖库"""
    missing_deps = []

    # 检查核心依赖
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")

    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")

    try:
        import scipy
    except ImportError:
        missing_deps.append("scipy")

    # 检查COMTRADE库
    try:
        import comtrade
    except ImportError:
        missing_deps.append("comtrade")

    if missing_deps:
        missing_str = "\n".join(f"  - {dep}" for dep in missing_deps)
        error_msg = f"""缺少以下依赖库：
{missing_str}

请运行以下命令安装：
pip install {' '.join(missing_deps)}"""
        return False, error_msg

    return True, ""


def setup_application_style(app):
    """设置应用程序样式"""
    # 设置应用程序信息
    app.setApplicationName("COMTRADE波形分析器")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("电力系统分析工具")

    # 设置默认字体
    font = QFont("微软雅黑", 9)
    app.setFont(font)

    # 设置样式表
    style_sheet = """
    QMainWindow {
        background-color: #f5f5f5;
    }

    QMenuBar {
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 4px;
    }

    QMenuBar::item {
        background-color: transparent;
        padding: 8px 12px;
        border-radius: 4px;
    }

    QMenuBar::item:selected {
        background-color: #e3f2fd;
    }

    QToolBar {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        spacing: 3px;
        padding: 4px;
    }

    QPushButton {
        background-color: #2196f3;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #1976d2;
    }

    QPushButton:pressed {
        background-color: #0d47a1;
    }

    QPushButton:disabled {
        background-color: #bdbdbd;
        color: #757575;
    }

    QGroupBox {
        font-weight: bold;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        margin-top: 1ex;
        padding-top: 10px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
    """

    app.setStyleSheet(style_sheet)


def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

    try:
        # 设置应用程序样式
        setup_application_style(app)

        # 初始化日志系统
        logger = setup_logger()
        logger.info("应用程序启动")

        # 检查依赖库
        deps_ok, error_msg = check_dependencies()
        if not deps_ok:
            QMessageBox.critical(None, "依赖库检查失败", error_msg)
            return 1

        # 加载应用设置
        settings = AppSettings()

        # 创建主窗口
        main_window = MainWindow(settings)
        main_window.show()

        logger.info("主窗口已显示")

        # 运行应用程序
        exit_code = app.exec()
        logger.info(f"应用程序退出，代码: {exit_code}")

        return exit_code

    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)
        QMessageBox.critical(None, "启动失败", f"应用程序启动失败：\n{str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())