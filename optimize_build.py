#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包优化脚本
用于优化PyInstaller打包结果，提高运行性能
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def optimize_imports():
    """优化导入，减少启动时间"""
    # 创建一个启动优化文件
    startup_code = '''
import sys
import os

# 优化Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 预导入常用模块，加快启动速度
import numpy
import matplotlib
matplotlib.use('Qt5Agg')  # 设置后端
import pandas
import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
'''

    with open('startup_optimizer.py', 'w', encoding='utf-8') as f:
        f.write(startup_code)


def create_batch_build():
    """创建批处理构建脚本"""
    batch_content = '''@echo off
echo ========================================
echo COMTRADE波形分析器 - 自动打包脚本
echo ========================================
echo.

REM 设置Python环境变量
set PYTHONIOENCODING=utf-8
set PYTHONOPTIMIZE=1

REM 清理旧的构建文件
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM 运行优化脚本
echo 运行优化脚本...
python optimize_build.py

REM 开始打包
echo 开始打包...
pyinstaller --clean --noconfirm build_config.spec

REM 检查打包结果
if exist "dist\\COMTRADE波形分析器.exe" (
    echo.
    echo ========================================
    echo 打包成功！
    echo 输出文件: dist\\COMTRADE波形分析器.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 打包失败！请检查错误信息。
    echo ========================================
)

pause
'''

    with open('build.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)


def create_version_info():
    """创建版本信息文件"""
    version_content = '''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 0, 0),
    prodvers=(2, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404B0',
        [StringStruct(u'CompanyName', u'电力系统分析工具'),
        StringStruct(u'FileDescription', u'COMTRADE波形分析器'),
        StringStruct(u'FileVersion', u'2.0.0.0'),
        StringStruct(u'InternalName', u'COMTRADE Analyzer'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2025'),
        StringStruct(u'OriginalFilename', u'COMTRADE波形分析器.exe'),
        StringStruct(u'ProductName', u'COMTRADE波形分析器'),
        StringStruct(u'ProductVersion', u'2.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
'''

    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_content)


if __name__ == '__main__':
    print("开始优化构建配置...")
    optimize_imports()
    create_batch_build()
    create_version_info()
    print("优化配置完成！")